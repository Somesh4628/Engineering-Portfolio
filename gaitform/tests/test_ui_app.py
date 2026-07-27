"""Tests for the UI application module."""
import sys
from unittest.mock import patch, MagicMock

@patch("gaitform.ui.app.st")
@patch("gaitform.ui.app.requests")
def test_ui_main(mock_requests, mock_st):
    from gaitform.ui.app import main
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"files": []}
    mock_requests.get.return_value = mock_resp
    
    # Let's execute main directly.
    # We can mock st methods that we use
    mock_st.sidebar.text_input.return_value = "http://localhost:8000"
    mock_st.sidebar.number_input.return_value = 1.75
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.return_value = False
    
    # Avoid infinite blocking or exceptions
    main()
    
    assert mock_st.set_page_config.called
    assert mock_st.title.called
