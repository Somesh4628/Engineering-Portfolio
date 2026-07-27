import os
import pytest
from gaitform.extraction.base import KeypointSequence
from gaitform.extraction.mediapipe_extractor import MediaPipeGaitExtractor


def test_mediapipe_extraction():
    video_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'sample_data',
        'sample_video.mp4')
    model_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'pose_landmarker_heavy.task')

    # If the video doesn't exist, we skip rather than fail
    if not os.path.exists(video_path):
        pytest.skip(f"Sample video not found at {video_path}")

    if not os.path.exists(model_path):
        pytest.skip(f"Model not found at {model_path}")

    extractor = MediaPipeGaitExtractor(model_path=model_path)
    seq = extractor.extract(video_path)

    assert isinstance(seq, KeypointSequence)
    assert len(seq.frames) > 0
    assert seq.fps > 0

    # Check that we extracted landmarks (MediaPipe gives 33 landmarks)
    first_frame = seq.frames[0]
    assert len(first_frame.landmarks) > 0
    assert "LEFT_ANKLE" in first_frame.landmarks or "LEFT_HEEL" in first_frame.landmarks
