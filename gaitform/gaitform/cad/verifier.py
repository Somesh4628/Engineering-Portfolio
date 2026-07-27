"""Module docstring."""
import os

import trimesh


class STLVerifier:
    @staticmethod
    def verify(mesh_path: str):
        if not os.path.exists(mesh_path):
            return {"status": "error", "message": "File not found"}

        try:
            mesh = trimesh.load(mesh_path)
            assert isinstance(mesh, trimesh.Trimesh), "Loaded geometry is not a Trimesh"

            bounds = mesh.bounds
            length_mm = bounds[1][1] - bounds[0][1]
            width_mm = bounds[1][0] - bounds[0][0]
            max_height_mm = bounds[1][2] - bounds[0][2]

            # Check if it's left or right based on center of mass vs bounding box center
            center_x = (bounds[1][0] + bounds[0][0]) / 2.0
            com_x = mesh.center_mass[0]

            # Usually the arch is on the medial side, pushing the COM slightly
            inferred_side = "left" if com_x > center_x else "right"

            return {
                "status": "success",
                "is_watertight": mesh.is_watertight,
                "length_mm": round(float(length_mm), 2),
                "width_mm": round(float(width_mm), 2),
                "max_height_mm": round(float(max_height_mm), 2),
                "inferred_side": inferred_side,
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.faces),
            }
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}
