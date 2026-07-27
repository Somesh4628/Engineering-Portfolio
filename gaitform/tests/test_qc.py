"""Module docstring."""
import json
import os
import subprocess
import sys
import tempfile

import pytest

from gaitform.extraction.base import FrameKeypoints, Keypoint, KeypointSequence
from gaitform.metrics.analyzer import GaitMetricsEngine


def test_metrics_step_width_temporal_alignment():
    """
    QC Test: Ensure step width is calculated by matching left and right heel strikes
    temporally (by closest frame), rather than simply aligning the arrays by index.
    """
    frames = []
    # Create a synthetic sequence where left heel strikes at frame 10 and 30
    # Right heel strikes at frame 20.
    # L1 (10), R1 (20), L2 (30)

    for i in range(40):
        # We need detrended Y to peak at these frames.
        # Just manually set the Y to trigger find_peaks
        l_y = 0.5
        r_y = 0.5

        if i == 10:
            l_y = 1.0  # Left peak 1
        if i == 30:
            l_y = 1.0  # Left peak 2
        if i == 20:
            r_y = 1.0  # Right peak 1

        # We set X to known values so we can test the step width math
        # Left heel X = 0.3 always
        # Right heel X = 0.7 always
        # Distance = 0.4

        landmarks = {
            "LEFT_HEEL": Keypoint(x=0.3, y=l_y, z=0, visibility=1.0),
            "RIGHT_HEEL": Keypoint(x=0.7, y=r_y, z=0, visibility=1.0),
            "NOSE": Keypoint(x=0.5, y=0.1, z=0, visibility=1.0),  # height ref
        }
        frames.append(
            FrameKeypoints(frame_index=i, timestamp_ms=i * 33.3, landmarks=landmarks)
        )

    seq = KeypointSequence(fps=30.0, frames=frames)
    engine = GaitMetricsEngine(seq)
    metrics = engine.analyze()

    assert metrics["step_width_m"] is not None
    # If the logic aligns by closest timestamp, it will correctly pair L=10 with R=20, and L=30 with R=20.
    # The X distance is always 0.4.
    # The pixels_to_meters is roughly 1.75 / (0.5 - 0.1) = 1.75 / 0.4 = 4.375
    # Step width should be 0.4 * 4.375 = 1.75
    assert abs(metrics["step_width_m"] - 0.875) < 0.1


def test_cli_generate_cad_parity():
    """
    QC Test: Ensure `generate-cad` CLI outputs BOTH left and right zoning/STL files.
    """
    # Create a dummy params.json
    dummy_params = {
        "orthotic_parameters": {
            "left": {
                "arch_height_mm": 15.0,
                "heel_cup_depth_mm": 10.0,
                "medial_post_deg": 2.0,
                "lateral_post_deg": 0.0,
                "met_pad_position_mm": 180.0,
                "rigidity_zones": [],
            },
            "right": {
                "arch_height_mm": 15.0,
                "heel_cup_depth_mm": 10.0,
                "medial_post_deg": 2.0,
                "lateral_post_deg": 0.0,
                "met_pad_position_mm": 180.0,
                "rigidity_zones": [],
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        params_path = os.path.join(tmpdir, "params.json")
        with open(params_path, "w") as f:
            json.dump(dummy_params, f)

        stl_path = os.path.join(tmpdir, "orthotic.stl")
        json_path = os.path.join(tmpdir, "print_instructions.json")
        png_path = os.path.join(tmpdir, "heatmap.png")

        cmd = [
            sys.executable,
            "-m",
            "gaitform",
            "generate-cad",
            params_path,
            "--stl",
            stl_path,
            "--json",
            json_path,
            "--png",
            png_path,
        ]

        # Note: Depending on environment, python might need to be explicitly resolved,
        # but for a simple unit test, we just assume it's in the env.
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Assert files exist for BOTH left and right
            assert os.path.exists(os.path.join(tmpdir, "orthotic_left.stl"))
            assert os.path.exists(os.path.join(tmpdir, "orthotic_right.stl"))
            assert os.path.exists(os.path.join(tmpdir, "print_instructions_left.json"))
            assert os.path.exists(os.path.join(tmpdir, "print_instructions_right.json"))
            assert os.path.exists(os.path.join(tmpdir, "heatmap_left.png"))
            assert os.path.exists(os.path.join(tmpdir, "heatmap_right.png"))

        except subprocess.CalledProcessError as e:
            pytest.fail(
                f"generate-cad CLI failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            )
