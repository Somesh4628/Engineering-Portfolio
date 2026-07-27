"""Module docstring."""
import os

from streamlit.testing.v1 import AppTest


def test_app_loads_without_error():
    app_path = os.path.join(os.path.dirname(__file__), "..", "gaitform", "ui", "app.py")
    at = AppTest.from_file(app_path)
    at.run(timeout=15)
    assert not at.exception
