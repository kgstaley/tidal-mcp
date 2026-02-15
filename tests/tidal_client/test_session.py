# tests/tidal_client/test_session.py
import json
import stat
import pytest
import responses
from datetime import datetime, timedelta
from unittest.mock import patch
from tidal_client.session import TidalSession
from tidal_client.exceptions import NotFoundError, RateLimitError, TidalAPIError, AuthenticationError


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
    session._token_expires_at = datetime.now() + timedelta(seconds=3600)  # Valid token

    result = session.request("GET", "artists/123")

    assert result == {"id": "123", "name": "Test Artist"}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "https://api.tidal.com/v1/artists/123"


@responses.activate
def test_request_raises_not_found_on_404(mock_config):
    """request should raise NotFoundError on 404"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/999",
        json={"error": "not found"},
        status=404
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"
    session._token_expires_at = datetime.now() + timedelta(seconds=3600)  # Valid token

    with pytest.raises(NotFoundError) as exc_info:
        session.request("GET", "artists/999")

    assert "artists/999" in str(exc_info.value)


@responses.activate
def test_request_raises_rate_limit_on_429(mock_config):
    """request should raise RateLimitError on 429"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"error": "rate limit exceeded"},
        status=429
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"
    session._token_expires_at = datetime.now() + timedelta(seconds=3600)  # Valid token

    with pytest.raises(RateLimitError):
        session.request("GET", "artists/123")


@responses.activate
def test_request_raises_generic_error_on_other_http_errors(mock_config):
    """request should raise TidalAPIError on other HTTP errors"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"error": "internal server error"},
        status=500
    )

    session = TidalSession(mock_config)
    session._access_token = "test_token"
    session._token_expires_at = datetime.now() + timedelta(seconds=3600)  # Valid token

    with pytest.raises(TidalAPIError) as exc_info:
        session.request("GET", "artists/123")

    assert "500" in str(exc_info.value)


def test_save_session_writes_token_data(mock_config, tmp_path):
    """save_session should write token data to JSON file"""
    session = TidalSession(mock_config)
    session._access_token = "test_access_token"
    session._refresh_token = "test_refresh_token"
    session._token_expires_at = datetime(2024, 12, 31, 23, 59, 59)
    session._user_id = "12345"

    session_file = tmp_path / "test-session.json"
    session.save_session(str(session_file))

    # Verify file exists and contains correct data
    assert session_file.exists()
    with open(session_file) as f:
        data = json.load(f)

    assert data["access_token"] == "test_access_token"
    assert data["refresh_token"] == "test_refresh_token"
    assert data["token_expires_at"] == "2024-12-31T23:59:59"
    assert data["user_id"] == "12345"


def test_load_session_reads_token_data(mock_config, tmp_path):
    """load_session should restore token data from JSON file"""
    # Create session file
    session_file = tmp_path / "test-session.json"
    session_data = {
        "access_token": "loaded_access_token",
        "refresh_token": "loaded_refresh_token",
        "token_expires_at": "2024-12-31T23:59:59",
        "user_id": "67890"
    }
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    # Load session
    session = TidalSession(mock_config)
    session.load_session(str(session_file))

    assert session._access_token == "loaded_access_token"
    assert session._refresh_token == "loaded_refresh_token"
    assert session._token_expires_at == datetime(2024, 12, 31, 23, 59, 59)
    assert session._user_id == "67890"


def test_load_session_handles_missing_file(mock_config, tmp_path):
    """load_session should handle missing file gracefully"""
    session = TidalSession(mock_config)

    # Should not raise exception
    session.load_session(str(tmp_path / "nonexistent.json"))

    # Tokens should remain None
    assert session._access_token is None
    assert session._refresh_token is None


def test_save_session_handles_none_values(mock_config, tmp_path):
    """save_session should handle None token values"""
    session = TidalSession(mock_config)
    # All tokens are None by default

    session_file = tmp_path / "test-session.json"
    session.save_session(str(session_file))

    # Verify file exists and contains null values
    assert session_file.exists()
    with open(session_file) as f:
        data = json.load(f)

    assert data["access_token"] is None
    assert data["refresh_token"] is None
    assert data["token_expires_at"] is None
    assert data["user_id"] is None


def test_save_session_sets_restrictive_permissions(mock_config, tmp_path):
    """save_session should set file permissions to 0o600"""
    session = TidalSession(mock_config)
    session._access_token = "test_token"

    session_file = tmp_path / "test-session.json"
    session.save_session(str(session_file))

    # Check file permissions are owner read/write only (0o600)
    file_stat = session_file.stat()
    assert stat.S_IMODE(file_stat.st_mode) == 0o600


def test_load_session_handles_corrupt_json(mock_config, tmp_path):
    """load_session should handle corrupt JSON gracefully"""
    # Create corrupt JSON file
    session_file = tmp_path / "corrupt.json"
    with open(session_file, "w") as f:
        f.write("{invalid json")

    session = TidalSession(mock_config)
    # Should not raise exception
    session.load_session(str(session_file))

    # Tokens should remain None
    assert session._access_token is None


def test_load_session_handles_invalid_datetime(mock_config, tmp_path):
    """load_session should handle invalid datetime format gracefully"""
    session_file = tmp_path / "bad-datetime.json"
    session_data = {
        "access_token": "test_token",
        "token_expires_at": "not-a-datetime"
    }
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    session = TidalSession(mock_config)
    session.load_session(str(session_file))

    # Token should be loaded, but expires_at should be None
    assert session._access_token == "test_token"
    assert session._token_expires_at is None


@responses.activate
def test_login_oauth_device_flow(mock_config):
    """login_oauth_device_flow should request device code"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={
            "device_code": "device123",
            "user_code": "USER1234",
            "verification_uri": "https://link.tidal.com/activate",
            "expires_in": 300,
            "interval": 5
        },
        status=200
    )

    session = TidalSession(mock_config)
    result = session.login_oauth_device_flow()

    assert result["user_code"] == "USER1234"
    assert result["verification_uri"] == "https://link.tidal.com/activate"


@responses.activate
@patch("time.sleep")
def test_complete_oauth_flow(mock_sleep, mock_config):
    """complete_oauth_flow should poll for token and store in session"""
    # Mock token endpoint
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "final_token",
            "refresh_token": "final_refresh",
            "expires_in": 7200,
            "user_id": "user123"
        },
        status=200
    )

    session = TidalSession(mock_config)
    device_code_data = {
        "device_code": "device123",
        "interval": 1,
        "expires_in": 300
    }

    session.complete_oauth_flow(device_code_data)

    assert session._access_token == "final_token"
    assert session._refresh_token == "final_refresh"
    assert session._user_id == "user123"
    assert session._token_expires_at is not None
    assert session._is_token_valid() is True


def test_complete_oauth_flow_validates_device_code(mock_config):
    """complete_oauth_flow should validate device_code is present"""
    session = TidalSession(mock_config)

    # Missing device_code
    device_code_data = {
        "interval": 5,
        "expires_in": 300
    }

    with pytest.raises(AuthenticationError) as exc_info:
        session.complete_oauth_flow(device_code_data)

    assert "device_code" in str(exc_info.value)


@responses.activate
@patch("time.sleep")
def test_complete_oauth_flow_validates_token_fields(mock_sleep, mock_config):
    """complete_oauth_flow should validate token_data has required fields"""
    # Mock response missing access_token
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "refresh_token": "test_refresh",
            "expires_in": 3600
        },
        status=200
    )

    session = TidalSession(mock_config)
    device_code_data = {
        "device_code": "device123",
        "interval": 1,
        "expires_in": 300
    }

    with pytest.raises(AuthenticationError) as exc_info:
        session.complete_oauth_flow(device_code_data)

    assert "access_token" in str(exc_info.value)


@responses.activate
def test_refresh_token(mock_config):
    """refresh_token should update session with new tokens"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "refreshed_access",
            "refresh_token": "refreshed_refresh",
            "expires_in": 7200
        },
        status=200
    )

    session = TidalSession(mock_config)
    session._refresh_token = "old_refresh_token"

    session.refresh_token()

    assert session._access_token == "refreshed_access"
    assert session._refresh_token == "refreshed_refresh"
    assert session._is_token_valid() is True


def test_refresh_token_raises_without_refresh_token(mock_config):
    """refresh_token should raise error if no refresh token available"""
    session = TidalSession(mock_config)
    # No refresh token set

    with pytest.raises(AuthenticationError) as exc_info:
        session.refresh_token()

    assert "No refresh token available" in str(exc_info.value)


@responses.activate
def test_request_auto_refreshes_expired_token(mock_config):
    """request should automatically refresh token if expired"""
    # Mock refresh token endpoint
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        },
        status=200
    )

    # Mock successful API call with new token
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist"},
        status=200
    )

    session = TidalSession(mock_config)
    session._access_token = "old_expired_token"
    session._refresh_token = "valid_refresh_token"
    session._token_expires_at = datetime.now() - timedelta(seconds=100)  # Expired

    # Should auto-refresh and succeed
    result = session.request("GET", "artists/123")

    assert result["name"] == "Test Artist"
    assert session._access_token == "new_access_token"
    assert session._is_token_valid() is True
    assert len(responses.calls) == 2  # 1 refresh + 1 API call


def test_request_raises_auth_error_when_no_refresh_token(mock_config):
    """request should raise AuthenticationError if token expired and no refresh token"""
    session = TidalSession(mock_config)
    session._access_token = "expired_token"
    session._token_expires_at = datetime.now() - timedelta(seconds=100)
    # No refresh token set

    with pytest.raises(AuthenticationError) as exc_info:
        session.request("GET", "artists/123")

    assert "token expired" in str(exc_info.value).lower() or "not authenticated" in str(exc_info.value).lower()
