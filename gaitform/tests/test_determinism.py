"""Module docstring."""
import os

import pytest

from gaitform.extraction.mediapipe_extractor import MediaPipeGaitExtractor
from gaitform.metrics.analyzer import GaitMetricsEngine


def test_metrics_determinism():
    video_path = os.path.join(
        os.path.dirname(__file__), "..", "sample_data", "demo.mp4"
    )
    if not os.path.exists(video_path):
        pytest.skip(f"Sample video not found at {video_path}")

    model_path = os.path.join(
        os.path.dirname(__file__), "..", "pose_landmarker_heavy.task"
    )

    extractor = MediaPipeGaitExtractor(model_path=model_path)
    seq = extractor.extract(video_path)

    engine1 = GaitMetricsEngine(seq)
    metrics1 = engine1.analyze()

    engine2 = GaitMetricsEngine(seq)
    metrics2 = engine2.analyze()

    # Assert exact match to prove all np.random mocks are removed
    assert metrics1 == metrics2, "Metrics should be 100% deterministic"
    assert "cadence_steps_per_min" in metrics1
    assert "stride_length_l_m" in metrics1
    assert "pronation_angle_l_deg" in metrics1
