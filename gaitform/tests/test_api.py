"""Tests for the Fastapi server module."""
from unittest.mock import patch, MagicMock

@patch("fastapi.FastAPI")
def test_api_endpoints(mock_fastapi):
    # Just import it so it registers endpoints
    import gaitform.server.api
    assert gaitform.server.api.app is not None
