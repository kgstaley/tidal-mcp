from datetime import datetime, timedelta

import pytest
import requests
import responses

from tidal_client.endpoints.artists import ArtistsEndpoint
from tidal_client.exceptions import NotFoundError, RateLimitError, TidalAPIError
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
        responses.GET, "https://api.tidal.com/v1/artists/123", json={"id": "123", "name": "Test Artist"}, status=200
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"  # Set token directly for now

    result = session.request("GET", "artists/123")

    assert result == {"id": "123", "name": "Test Artist"}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "https://api.tidal.com/v1/artists/123"


@responses.activate
def test_request_raises_not_found_on_404(mock_config):
    """request should raise NotFoundError on 404"""
    responses.add(responses.GET, "https://api.tidal.com/v1/artists/999", json={"error": "not found"}, status=404)

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(NotFoundError) as exc_info:
        session.request("GET", "artists/999")

    assert "artists/999" in str(exc_info.value)


@responses.activate
def test_request_raises_rate_limit_on_429(mock_config):
    """request should raise RateLimitError on 429"""
    responses.add(
        responses.GET, "https://api.tidal.com/v1/artists/123", json={"error": "rate limit exceeded"}, status=429
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(RateLimitError):
        session.request("GET", "artists/123")


@responses.activate
def test_request_raises_generic_error_on_other_http_errors(mock_config):
    """request should raise TidalAPIError on other HTTP errors"""
    responses.add(
        responses.GET, "https://api.tidal.com/v1/artists/123", json={"error": "internal server error"}, status=500
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "500" in str(exc_info.value)


@responses.activate
def test_request_raises_error_on_timeout(mock_config):
    """request should raise TidalAPIError on timeout"""
    responses.add(responses.GET, "https://api.tidal.com/v1/artists/123", body=requests.Timeout("Request timed out"))

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "timeout" in str(exc_info.value).lower()


@responses.activate
def test_request_raises_error_on_connection_error(mock_config):
    """request should raise TidalAPIError on connection error"""
    responses.add(
        responses.GET, "https://api.tidal.com/v1/artists/123", body=requests.ConnectionError("Connection refused")
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "connection" in str(exc_info.value).lower()


@responses.activate
def test_request_raises_error_on_invalid_json(mock_config):
    """request should raise TidalAPIError on invalid JSON response"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        body="<html>Server Error</html>",
        status=200,
        content_type="text/html",
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "json" in str(exc_info.value).lower()


@responses.activate
def test_request_refreshes_expired_token_automatically(mock_config):
    """request should automatically refresh expired token before making API call"""
    # Mock refresh token endpoint
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"access_token": "refreshed_token", "refresh_token": "new_refresh_token", "expires_in": 3600},
        status=200,
    )

    # Mock API call with new token
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist"},
        status=200,
    )

    session = TidalSession(mock_config)
    # Set expired token
    session._access_token = "expired_token"
    session._refresh_token = "valid_refresh_token"
    session._token_expires_at = datetime.now() - timedelta(seconds=10)  # Expired

    result = session.request("GET", "artists/123")

    # Should have made 2 requests: refresh + API call
    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == "https://auth.tidal.com/v1/oauth2/token"
    assert responses.calls[1].request.url == "https://api.tidal.com/v1/artists/123"

    # Token should be refreshed
    assert session._access_token == "refreshed_token"
    assert session._refresh_token == "new_refresh_token"

    # API call should succeed
    assert result["name"] == "Test Artist"


@responses.activate
def test_request_uses_valid_token_without_refresh(mock_config):
    """request should NOT refresh when token is still valid"""
    # Mock API call (no refresh endpoint needed)
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist"},
        status=200,
    )

    session = TidalSession(mock_config)
    # Set valid token
    session._access_token = "valid_token"
    session._refresh_token = "refresh_token"
    session._token_expires_at = datetime.now() + timedelta(hours=1)  # Valid for 1 hour

    result = session.request("GET", "artists/123")

    # Should have made only 1 request (no refresh)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "https://api.tidal.com/v1/artists/123"

    # Token should remain unchanged
    assert session._access_token == "valid_token"

    # API call should succeed
    assert result["name"] == "Test Artist"


@responses.activate
def test_request_raises_error_when_refresh_fails(mock_config):
    """request should raise error if token refresh fails"""
    # Mock failed refresh
    responses.add(
        responses.POST, "https://auth.tidal.com/v1/oauth2/token", json={"error": "invalid_grant"}, status=400
    )

    session = TidalSession(mock_config)
    # Set expired token
    session._access_token = "expired_token"
    session._refresh_token = "invalid_refresh_token"
    session._token_expires_at = datetime.now() - timedelta(seconds=10)

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "refresh" in str(exc_info.value).lower()


def test_session_has_artists_property(mock_config):
    """Session should have lazy-loaded artists endpoint"""
    session = TidalSession(mock_config)

    assert isinstance(session.artists, ArtistsEndpoint)
    assert session.artists.session == session


def test_session_artists_is_cached(mock_config):
    """Session should cache artists endpoint instance"""
    session = TidalSession(mock_config)

    artists1 = session.artists
    artists2 = session.artists

    # Should return the same instance
    assert artists1 is artists2
