"""Tests for session save/load functionality"""
import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from tidal_client.session import TidalSession


@pytest.fixture
def temp_session_file():
    """Create a temporary session file path"""
    temp_dir = tempfile.gettempdir()
    session_file = os.path.join(temp_dir, "test-tidal-session.json")

    yield session_file

    # Cleanup
    if os.path.exists(session_file):
        os.remove(session_file)


def test_save_session_creates_file(mock_config, temp_session_file):
    """save_session should create JSON file with session data"""
    session = TidalSession(mock_config)
    session._access_token = "test_access_token"
    session._refresh_token = "test_refresh_token"
    session._token_expires_at = datetime.now() + timedelta(hours=1)
    session._user_id = "12345"

    session.save_session(temp_session_file)

    assert os.path.exists(temp_session_file)

    with open(temp_session_file) as f:
        data = json.load(f)

    assert data["access_token"] == "test_access_token"
    assert data["refresh_token"] == "test_refresh_token"
    assert data["user_id"] == "12345"
    assert "expires_at" in data


def test_load_session_restores_tokens(mock_config, temp_session_file):
    """load_session should restore session data from JSON file"""
    expires_at = datetime.now() + timedelta(hours=1)

    session_data = {
        "access_token": "loaded_access_token",
        "refresh_token": "loaded_refresh_token",
        "user_id": "67890",
        "expires_at": expires_at.isoformat(),
    }

    with open(temp_session_file, "w") as f:
        json.dump(session_data, f)

    session = TidalSession(mock_config)
    session.load_session(temp_session_file)

    assert session._access_token == "loaded_access_token"
    assert session._refresh_token == "loaded_refresh_token"
    assert session._user_id == "67890"
    assert session._token_expires_at is not None


def test_load_session_does_nothing_if_file_missing(mock_config, temp_session_file):
    """load_session should not raise error if file doesn't exist"""
    session = TidalSession(mock_config)

    # Should not raise exception
    session.load_session(temp_session_file)

    assert session._access_token is None
    assert session._refresh_token is None
