"""Module docstring."""
import os

import trimesh


class PhotogrammetryEngine:
    def __init__(self, work_dir: str = "photogrammetry_workspace"):
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

    def process_video_to_stl(self, video_path: str, output_stl_path: str):
        raise NotImplementedError(
            "Photogrammetry reconstruction not yet implemented. "
            "Provide a real foot scan STL via --scan-left / --scan-right instead."
        )
