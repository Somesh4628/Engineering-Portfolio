"""Tests for the pressure parser."""
from unittest.mock import patch, mock_open
from gaitform.sensors.pressure_parser import parse_fscan_csv
import numpy as np

def test_parse_csv():
    # Provide exactly 1260 comma-separated values to pass len(values) == 60 * 21 check
    dummy_csv = ",".join(["1.0"] * 1260) + "\n"
    
    with patch("builtins.open", mock_open(read_data=dummy_csv)):
        data = parse_fscan_csv("dummy.csv")
        assert data is not None
