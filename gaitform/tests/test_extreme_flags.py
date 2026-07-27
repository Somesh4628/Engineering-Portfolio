"""Module docstring."""
import json

from gaitform.mapping.rules import OrthoticParameterMapper


def test_extreme_flags():
    # Extreme input: 15.5 degrees pronation, huge asymmetry
    metrics = {
        "cadence_steps_per_min": 95.0,
        "pronation_angle_l_deg": 15.5,
        "pronation_angle_r_deg": 2.0,
        "foot_length_mm": 280.0,
    }

    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)
    left_params = params_dict["left"]

    print("--- SYNTHETIC EXTREME INPUT RESULTS ---")
    print(json.dumps(left_params.to_dict(), indent=2))
    print("\n--- FLAGS TRIGGERED ---")
    for flag in left_params.flags_for_review:
        print(f"- {flag}")

    # Assertions to make this a real test
    assert (
        len(left_params.flags_for_review) == 2
    ), "Expected exactly 2 flags for this extreme input"
    assert (
        left_params.medial_post_deg == 4.0
    ), "Expected medial post to be capped at 4.0"
    assert (
        left_params.met_pad_position_mm == 182.0
    ), "Expected met pad to be 65% of 280mm"


if __name__ == "__main__":
    test_extreme_flags()
