"""Tests for dual-mode client support"""

from unittest.mock import Mock, patch

import pytest

from tidal_api.utils import _create_tidal_session


def test_create_session_uses_browser_session_by_default(monkeypatch):
    """_create_tidal_session should use BrowserSession when env var not set"""
    # Don't set TIDAL_USE_CUSTOM_CLIENT
    monkeypatch.delenv("TIDAL_USE_CUSTOM_CLIENT", raising=False)

    # Mock BrowserSession at import time
    mock_browser = Mock()
    with patch.dict("sys.modules", {"tidal_api.browser_session": Mock(BrowserSession=mock_browser)}):
        _create_tidal_session()

    # Should create BrowserSession
    mock_browser.assert_called_once()


def test_create_session_uses_browser_session_when_false(monkeypatch):
    """_create_tidal_session should use BrowserSession when env var is false"""
    monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "false")

    # Mock BrowserSession at import time
    mock_browser = Mock()
    with patch.dict("sys.modules", {"tidal_api.browser_session": Mock(BrowserSession=mock_browser)}):
        _create_tidal_session()

    mock_browser.assert_called_once()


def test_create_session_uses_custom_client_when_true(monkeypatch):
    """_create_tidal_session should use custom client when env var is true"""
    monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
    monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")

    # Mock custom client modules at import time
    mock_session = Mock()
    mock_config = Mock()
    with patch.dict(
        "sys.modules",
        {"tidal_client.session": Mock(TidalSession=mock_session), "tidal_client.config": Mock(Config=mock_config)},
    ):
        _create_tidal_session()

    # Should create TidalSession
    mock_session.assert_called_once()


def test_create_session_custom_client_requires_credentials(monkeypatch):
    """_create_tidal_session should raise error when custom client is enabled without credentials"""
    monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
    monkeypatch.delenv("TIDAL_CLIENT_ID", raising=False)
    monkeypatch.delenv("TIDAL_CLIENT_SECRET", raising=False)

    with pytest.raises(ValueError, match="TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET required"):
        _create_tidal_session()


def test_create_session_custom_client_loads_existing_session(monkeypatch, tmp_path):
    """_create_tidal_session should load existing session file for custom client"""
    monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
    monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")

    # Create a real session file
    session_file = tmp_path / "tidal-session-oauth.json"
    session_file.write_text('{"access_token": "test"}')

    # Mock custom client modules
    mock_session_instance = Mock()
    mock_session = Mock(return_value=mock_session_instance)
    mock_config = Mock()

    with patch.dict(
        "sys.modules",
        {"tidal_client.session": Mock(TidalSession=mock_session), "tidal_client.config": Mock(Config=mock_config)},
    ):
        # Patch SESSION_FILE to point to our test file
        with patch("tidal_api.utils.SESSION_FILE", session_file):
            _create_tidal_session()

    # Should call load_session with the session file
    mock_session_instance.load_session.assert_called_once_with(session_file)
