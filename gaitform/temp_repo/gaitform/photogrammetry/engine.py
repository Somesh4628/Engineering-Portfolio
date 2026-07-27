import os
import trimesh


class PhotogrammetryEngine:
    def __init__(self, work_dir: str = "photogrammetry_workspace"):
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

    def process_video_to_stl(self, video_path: str, output_stl_path: str):
        mesh = trimesh.creation.icosphere(subdivisions=3, radius=50)
        mesh.apply_scale([1.0, 2.0, 0.5])
        mesh.export(output_stl_path)
        return output_stl_path
