from datetime import datetime, timedelta

import responses

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

    assert hasattr(session, "http")
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


@responses.activate
def test_request_makes_http_call(mock_config):
    """request should make HTTP call to TIDAL API"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist"},
        status=200
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"  # Set token directly for now

    result = session.request("GET", "artists/123")

    assert result == {"id": "123", "name": "Test Artist"}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "https://api.tidal.com/v1/artists/123"
