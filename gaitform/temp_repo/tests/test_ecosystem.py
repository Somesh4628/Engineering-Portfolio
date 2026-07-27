import os
import trimesh
import numpy as np
from fastapi.testclient import TestClient
from gaitform.server.api import app
from gaitform.photogrammetry.engine import PhotogrammetryEngine
from gaitform.cad.generator import CADGenerator
from gaitform.mapping.rules import OrthoticParams

client = TestClient(app)


def test_api_upload_and_list(tmp_path):
    # Overwrite UPLOAD_DIR in api for testing
    import gaitform.server.api as api
    api.UPLOAD_DIR = str(tmp_path)

    # Test upload UI endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert "upload" in response.text.lower()

    # Test file upload mock
    # Just testing the uploads list endpoint when empty
    res = client.get("/api/uploads")
    assert res.status_code == 200
    assert res.json() == {"uploads": []}


def test_photogrammetry_engine_mock():
    engine = PhotogrammetryEngine(work_dir="test_workspace")
    assert engine.work_dir == "test_workspace"

    # process_video_to_stl generates a mock ellipsoid
    out_stl = "test_ellipsoid.stl"
    engine.process_video_to_stl("dummy_video.mp4", out_stl)

    assert os.path.exists(out_stl)

    # Clean up
    if os.path.exists(out_stl):
        os.remove(out_stl)


def test_cad_generator_right_foot_arch_mirror():
    gen = CADGenerator()
    params = OrthoticParams(
        arch_height_mm=25.0,
        heel_cup_depth_mm=12.0,
        medial_post_deg=0.0,
        lateral_post_deg=0.0,
        met_pad_position_mm=130.0,
        rigidity_zones=[],
        flags_for_review=[]
    )

    # Generate left and right
    mesh_left = gen.generate_mesh(params, foot_side="left")
    mesh_right = gen.generate_mesh(params, foot_side="right")

    # We assert that both return valid meshes
    assert isinstance(mesh_left, trimesh.Trimesh)
    assert isinstance(mesh_right, trimesh.Trimesh)

    # Sample left foot: Medial is -X, Lateral is +X
    left_verts = mesh_left.vertices
    midfoot_left = left_verts[(left_verts[:, 1] > gen.length * 0.3)
                              & (left_verts[:, 1] < gen.length * 0.5)]
    medial_max_z_l = np.max(midfoot_left[midfoot_left[:, 0] < 0][:, 2]) if any(
        midfoot_left[:, 0] < 0) else 0
    lateral_max_z_l = np.max(midfoot_left[midfoot_left[:, 0] > 0][:, 2]) if any(
        midfoot_left[:, 0] > 0) else 0
    assert medial_max_z_l > lateral_max_z_l + \
        2.0, "Left foot arch should be medial (-X)"

    # Sample right foot: Medial is +X, Lateral is -X
    right_verts = mesh_right.vertices
    midfoot_right = right_verts[(right_verts[:, 1] > gen.length * 0.3)
                                & (right_verts[:, 1] < gen.length * 0.5)]
    medial_max_z_r = np.max(midfoot_right[midfoot_right[:, 0] > 0][:, 2]) if any(
        midfoot_right[:, 0] > 0) else 0
    lateral_max_z_r = np.max(midfoot_right[midfoot_right[:, 0] < 0][:, 2]) if any(
        midfoot_right[:, 0] < 0) else 0
    assert medial_max_z_r > lateral_max_z_r + \
        2.0, "Right foot arch should be medial (+X)"
