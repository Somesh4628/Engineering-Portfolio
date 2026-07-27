import os
import trimesh
import numpy as np
from gaitform.cad.generator import CADGenerator
from gaitform.mapping.rules import OrthoticParams


def test_cad_generation():
    params_list = [
        OrthoticParams(18.0, 12.0, 2.0, 0.0, 170.0, [], []),
        OrthoticParams(15.0, 10.0, 0.0, 0.0, 160.0, [], []),
        OrthoticParams(25.0, 15.0, 4.0, 0.0, 180.0, [], [])
    ]

    generator = CADGenerator()

    for params in params_list:
        mesh = generator.generate_mesh(params)

        assert isinstance(mesh, trimesh.Trimesh)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
        assert mesh.is_watertight

    output_json = "test_print.json"
    output_png = "test_heatmap.png"
    generator.generate_zoning(params_list[-1], output_json, output_png)

    assert os.path.exists(output_json)
    assert os.path.exists(output_png)

    os.remove(output_json)
    os.remove(output_png)


def test_right_foot_mirror_bug():
    params = OrthoticParams(
        arch_height_mm=20.0,
        heel_cup_depth_mm=10.0,
        medial_post_deg=5.0,
        lateral_post_deg=0.0,
        met_pad_position_mm=170.0,
        rigidity_zones=[],
        flags_for_review=[]
    )
    generator = CADGenerator()

    # Left foot
    mesh_l = generator.generate_mesh(params, foot_side="left")

    # Right foot
    mesh_r = generator.generate_mesh(params, foot_side="right")

    arch_region_l = mesh_l.vertices[(mesh_l.vertices[:,
                                                     1] > 0.2 * generator.length) & (mesh_l.vertices[:,
                                                                                                     1] < 0.5 * generator.length)]
    max_z_left_medial = np.max(arch_region_l[arch_region_l[:, 0] < -10][:, 2])
    max_z_left_lateral = np.max(arch_region_l[arch_region_l[:, 0] > 10][:, 2])
    assert max_z_left_medial > max_z_left_lateral

    arch_region_r = mesh_r.vertices[(mesh_r.vertices[:,
                                                     1] > 0.2 * generator.length) & (mesh_r.vertices[:,
                                                                                                     1] < 0.5 * generator.length)]
    # With the requested fix, right foot arch is built at x > 0
    max_z_right_negative = np.max(arch_region_r[arch_region_r[:, 0] < -10][:, 2])
    max_z_right_positive = np.max(arch_region_r[arch_region_r[:, 0] > 10][:, 2])
    assert max_z_right_positive > max_z_right_negative
