"""Module docstring."""
import os
from typing import Optional

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .base import FrameKeypoints, GaitExtractor, Keypoint, KeypointSequence

LANDMARK_NAMES = [
    "NOSE",
    "LEFT_EYE_INNER",
    "LEFT_EYE",
    "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER",
    "RIGHT_EYE",
    "RIGHT_EYE_OUTER",
    "LEFT_EAR",
    "RIGHT_EAR",
    "MOUTH_LEFT",
    "MOUTH_RIGHT",
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_ELBOW",
    "RIGHT_ELBOW",
    "LEFT_WRIST",
    "RIGHT_WRIST",
    "LEFT_PINKY",
    "RIGHT_PINKY",
    "LEFT_INDEX",
    "RIGHT_INDEX",
    "LEFT_THUMB",
    "RIGHT_THUMB",
    "LEFT_HIP",
    "RIGHT_HIP",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_ANKLE",
    "RIGHT_ANKLE",
    "LEFT_HEEL",
    "RIGHT_HEEL",
    "LEFT_FOOT_INDEX",
    "RIGHT_FOOT_INDEX",
]

_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "pose_landmarker_heavy.task"
)


class MediaPipeGaitExtractor(GaitExtractor):
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or _DEFAULT_MODEL_PATH
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. Run setup first."
            )

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            running_mode=vision.RunningMode.VIDEO,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def extract(self, video_path: str) -> KeypointSequence:
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or np.isnan(fps):
            fps = 30.0

        frames = []
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((frame_idx / fps) * 1000)
            pose_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

            if pose_result.pose_landmarks:
                landmarks = pose_result.pose_landmarks[0]
                frame_kps = {}
                for i, lm in enumerate(landmarks):
                    name = LANDMARK_NAMES[i] if i < len(LANDMARK_NAMES) else f"LM_{i}"
                    frame_kps[name] = Keypoint(
                        x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility
                    )
                frames.append(
                    FrameKeypoints(
                        frame_index=frame_idx,
                        timestamp_ms=timestamp_ms,
                        landmarks=frame_kps,
                    )
                )

            frame_idx += 1

        cap.release()
        return KeypointSequence(frames=frames, fps=fps)
