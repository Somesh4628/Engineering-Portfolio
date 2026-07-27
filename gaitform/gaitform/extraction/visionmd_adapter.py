"""Module docstring."""
from .base import GaitExtractor, KeypointSequence


class VisionMDGaitAdapter(GaitExtractor):
    def extract(self, video_path: str) -> KeypointSequence:
        return KeypointSequence(frames=[], fps=30.0)
