"""Module docstring."""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Keypoint:
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class FrameKeypoints:
    frame_index: int
    timestamp_ms: float
    landmarks: Dict[str, Keypoint]


@dataclass
class KeypointSequence:
    frames: List[FrameKeypoints]
    fps: float


class GaitExtractor:
    def extract(self, video_path: str) -> KeypointSequence:
        raise NotImplementedError
