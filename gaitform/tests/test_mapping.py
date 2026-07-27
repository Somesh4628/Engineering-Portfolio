"""Module docstring."""
from gaitform.mapping.rules import OrthoticParameterMapper


def test_mapping_normal():
    metrics = {
        "pronation_angle_l_deg": 5.0,
        "pronation_angle_r_deg": 5.0,
        "cadence_steps_per_min": 100.0,
    }
    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)

    assert params_dict["left"].arch_height_mm == 15.0
    assert params_dict["left"].heel_cup_depth_mm == 10.0
    assert params_dict["left"].medial_post_deg == 0.0
    assert len(params_dict["left"].flags_for_review) == 0


def test_mapping_high_pronation_clamping_and_flagging():
    # Pronation of 20 deg is extreme.
    # Medial post should calculate to (20-5)/2 = 7.5 deg, but clamp to 4.0
    # Should raise two flags (one for high pronation, one for post capping).
    metrics = {"pronation_angle_l_deg": 20.0, "cadence_steps_per_min": 100.0}
    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)

    assert params_dict["left"].medial_post_deg == 4.0
    assert params_dict["left"].arch_height_mm == 22.5
    assert params_dict["left"].heel_cup_depth_mm == 15.0
    assert len(params_dict["left"].flags_for_review) == 2
    assert any(
        "capped at 4 deg" in f.lower() for f in params_dict["left"].flags_for_review
    )
    assert any(
        "high left pronation" in f.lower() for f in params_dict["left"].flags_for_review
    )


def test_mapping_asymmetric():
    # Asymmetric input: Left pronation high (20 deg), Right pronation normal (2 deg)
    metrics = {
        "pronation_angle_l_deg": 20.0,
        "pronation_angle_r_deg": 2.0,
        "cadence_steps_per_min": 100.0,
    }
    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)

    # Left foot should have capped medial post and higher arch
    assert params_dict["left"].medial_post_deg == 4.0
    assert params_dict["left"].arch_height_mm == 22.5

    # Right foot should have no medial post and base arch
    assert params_dict["right"].medial_post_deg == 0.0
    assert params_dict["right"].arch_height_mm == 15.0

    # Assert they are indeed different
    assert params_dict["left"].medial_post_deg != params_dict["right"].medial_post_deg
    assert params_dict["left"].arch_height_mm != params_dict["right"].arch_height_mm
