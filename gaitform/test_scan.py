import trimesh
import os

os.makedirs("temp_extract", exist_ok=True)
mesh = trimesh.creation.box(extents=[100, 250, 10])
# We just need any valid Trimesh that's saved.
mesh.export("temp_extract/test_scan.stl")
print("Generated temp_extract/test_scan.stl")
