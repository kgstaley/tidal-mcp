"""Flask-specific fixtures for tidal_api tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mock browser_session before importing app
sys.modules["tidal_api.browser_session"] = MagicMock()

from tidal_api.app import create_app  # noqa: E402


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_session_file(tmp_path, mocker):
    """Create a mock session file."""
    session_file = tmp_path / "tidal-session-oauth.json"
    session_file.write_text("{}")
    mocker.patch("tidal_api.utils.SESSION_FILE", session_file)
    return session_file
