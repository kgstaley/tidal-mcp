"""Tests for OAuth authentication"""
import pytest
import responses

from tidal_client.auth import request_device_code, OAUTH_SCOPES
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
