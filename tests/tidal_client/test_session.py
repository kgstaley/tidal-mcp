# tests/tidal_client/test_session.py
import pytest
from datetime import datetime, timedelta
from tidal_client.session import TidalSession


def test_session_init_with_config(mock_config):
    """Session should initialize with config"""
    session = TidalSession(mock_config)

    assert session.config == mock_config
    assert session._access_token is None
    assert session._refresh_token is None
    assert session._token_expires_at is None
    assert session._user_id is None


def test_session_creates_http_session(mock_config):
    """Session should create requests.Session instance"""
    session = TidalSession(mock_config)

    assert hasattr(session, 'http')
    import requests
    assert isinstance(session.http, requests.Session)


def test_is_token_valid_returns_false_when_no_token(mock_config):
    """is_token_valid should return False when no token set"""
    session = TidalSession(mock_config)

    assert session._is_token_valid() is False


def test_is_token_valid_returns_false_when_expired(mock_config):
    """is_token_valid should return False when token expired"""
    session = TidalSession(mock_config)
    session._access_token = "test_token"
    session._token_expires_at = datetime.now() - timedelta(seconds=10)

    assert session._is_token_valid() is False


def test_is_token_valid_returns_true_when_valid(mock_config):
    """is_token_valid should return True when token valid"""
    session = TidalSession(mock_config)
    session._access_token = "test_token"
    session._token_expires_at = datetime.now() + timedelta(seconds=3600)

    assert session._is_token_valid() is True
