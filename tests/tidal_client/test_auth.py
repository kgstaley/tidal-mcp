"""Tests for OAuth authentication"""
import pytest
import responses
from unittest.mock import patch

from tidal_client.auth import request_device_code, poll_for_token, OAUTH_SCOPES
from tidal_client.exceptions import AuthenticationError


@responses.activate
def test_request_device_code_success(mock_config):
    """request_device_code should return device code data"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={
            "device_code": "test_device_code_123",
            "user_code": "ABCD-1234",
            "verification_uri": "https://link.tidal.com/activate",
            "expires_in": 300,
            "interval": 5
        },
        status=200
    )

    result = request_device_code(mock_config)

    assert result["device_code"] == "test_device_code_123"
    assert result["user_code"] == "ABCD-1234"
    assert result["verification_uri"] == "https://link.tidal.com/activate"
    assert result["expires_in"] == 300
    assert result["interval"] == 5

    # Verify request body (+ signs are URL encoded as %2B)
    assert len(responses.calls) == 1
    request_body = responses.calls[0].request.body
    assert f"client_id={mock_config.client_id}" in request_body
    # Scope uses + which gets URL encoded as %2B
    assert "scope=r_usr%2Bw_usr%2Bw_sub" in request_body


@responses.activate
def test_request_device_code_handles_errors(mock_config):
    """request_device_code should raise AuthenticationError on failure"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={"error": "invalid_client"},
        status=400
    )

    with pytest.raises(AuthenticationError) as exc_info:
        request_device_code(mock_config)

    assert "Failed to request device code" in str(exc_info.value)


@responses.activate
def test_request_device_code_handles_network_errors(mock_config):
    """request_device_code should raise AuthenticationError on network failure"""
    # No response added - will cause ConnectionError

    with pytest.raises(AuthenticationError):
        request_device_code(mock_config)


@responses.activate
def test_poll_for_token_success(mock_config):
    """poll_for_token should return token data when user authorizes"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "test_access_123",
            "refresh_token": "test_refresh_456",
            "expires_in": 3600,
            "user_id": "12345"
        },
        status=200
    )

    result = poll_for_token(mock_config, device_code="device123")

    assert result["access_token"] == "test_access_123"
    assert result["refresh_token"] == "test_refresh_456"
    assert result["expires_in"] == 3600
    assert result["user_id"] == "12345"


@responses.activate
@patch("time.sleep")  # Mock sleep to avoid waiting in tests
def test_poll_for_token_handles_pending(mock_sleep, mock_config):
    """poll_for_token should retry on authorization_pending"""
    # First two calls: pending, third call: success
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "authorization_pending"},
        status=400
    )
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "authorization_pending"},
        status=400
    )
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "success_token",
            "refresh_token": "success_refresh",
            "expires_in": 3600,
            "user_id": "12345"
        },
        status=200
    )

    result = poll_for_token(mock_config, device_code="device123", interval=1)

    assert result["access_token"] == "success_token"
    assert len(responses.calls) == 3
    assert mock_sleep.call_count == 2  # Slept twice before success


@responses.activate
@patch("time.time")
def test_poll_for_token_times_out(mock_time, mock_config):
    """poll_for_token should raise error if device code expires"""
    # Mock time.time() to simulate timeout
    mock_time.side_effect = [0, 301]  # Start at 0, then jump past expires_in=300

    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "authorization_pending"},
        status=400
    )

    with pytest.raises(AuthenticationError) as exc_info:
        poll_for_token(mock_config, device_code="device123", expires_in=300)

    assert "expired" in str(exc_info.value).lower()


@responses.activate
def test_poll_for_token_handles_errors(mock_config):
    """poll_for_token should raise error on access_denied"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "access_denied"},
        status=400
    )

    with pytest.raises(AuthenticationError) as exc_info:
        poll_for_token(mock_config, device_code="device123")

    assert "access_denied" in str(exc_info.value)
