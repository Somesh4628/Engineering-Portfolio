"""Tests for the navicular extraction module."""
from unittest.mock import patch, MagicMock
from gaitform.extraction.navicular import NavicularTracker

@patch("cv2.VideoCapture")
def test_navicular_tracker(mock_cap):
    mock_vid = MagicMock()
    mock_vid.isOpened.return_value = True
    
    # Simulate read() returning (True, frame) then (False, None)
    import numpy as np
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_vid.read.side_effect = [(True, dummy_frame), (False, None)]
    
    mock_cap.return_value = mock_vid
    
    with patch("cv2.cvtColor", return_value=dummy_frame), \
         patch("cv2.inRange", return_value=np.zeros((100,100), dtype=np.uint8)), \
         patch("cv2.findContours", return_value=([], None)):
             
        tracker = NavicularTracker()
        drop = tracker.track_navicular_drop("dummy.mp4")
        assert "drop_mm" in drop
