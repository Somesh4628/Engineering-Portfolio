"""Tests for the CLI module."""
from unittest.mock import patch, MagicMock
from gaitform.__main__ import generate_cad, map_parameters, compare_sessions, run_pipeline

@patch("gaitform.__main__.CADGenerator")
def test_generate_cad(mock_cad):
    mock_generator = MagicMock()
    mock_cad.return_value = mock_generator
    
    mock_json = {
        "orthotic_parameters": {
            "left": {"arch_height_mm": 10, "heel_cup_depth_mm": 5, "medial_post_deg": 0, "lateral_post_deg": 0, "met_pad_position_mm": 0, "rigidity_zones": []},
            "right": {"arch_height_mm": 10, "heel_cup_depth_mm": 5, "medial_post_deg": 0, "lateral_post_deg": 0, "met_pad_position_mm": 0, "rigidity_zones": []}
        }
    }
    
    with patch("builtins.open"), patch("json.load", return_value=mock_json), patch("gaitform.__main__.OrthoticParams"):
        generate_cad("dummy.json", "dummy.stl", "dummy_zones.json", "dummy.png", "left.stl", "right.stl")

@patch("gaitform.__main__.generate_cad")
@patch("gaitform.__main__.map_parameters")
@patch("gaitform.__main__.MediaPipeGaitExtractor")
@patch("gaitform.__main__.GaitMetricsEngine")
def test_run_pipeline(mock_engine, mock_extractor, mock_map, mock_cad):
    mock_eng_inst = MagicMock()
    mock_eng_inst.analyze.return_value = {"patient_height_m": 1.75, "cadence_steps_per_min": 100, "pronation_l": 5.0, "pronation_r": 5.0}
    mock_engine.return_value = mock_eng_inst
    
    run_pipeline("dummy.mp4")
