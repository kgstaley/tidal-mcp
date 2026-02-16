"""Tests for OAuth authentication flow"""

import responses

from tidal_client.config import Config
from tidal_client.exceptions import TidalAPIError
from tidal_client.session import TidalSession


@responses.activate
def test_request_device_code_returns_auth_data():
    """request_device_code should return device code and verification URL"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={
            "device_code": "test_device_code_123",
            "user_code": "ABCD-EFGH",
            "verification_uri": "https://link.tidal.com/device",
            "verification_uri_complete": "https://link.tidal.com/device?userCode=ABCD-EFGH",
            "expires_in": 300,
            "interval": 5,
        },
        status=200,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)

    result = session.request_device_code()

    assert result["device_code"] == "test_device_code_123"
    assert result["user_code"] == "ABCD-EFGH"
    assert result["verification_uri"] == "https://link.tidal.com/device"
    assert result["expires_in"] == 300
    assert result["interval"] == 5


@responses.activate
def test_request_device_code_sends_correct_payload():
    """request_device_code should send client_id and scope in request"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={"device_code": "test_code", "user_code": "TEST"},
        status=200,
    )

    config = Config(client_id="my_client_id", client_secret="my_secret")
    session = TidalSession(config)

    session.request_device_code()

    # Verify request payload
    assert len(responses.calls) == 1
    request = responses.calls[0].request

    # Check Content-Type header
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"

    # Check form data (responses stores body as string for form-encoded)
    body = request.body
    assert "client_id=my_client_id" in body
    assert "scope=r_usr+w_usr+w_sub" in body


@responses.activate
def test_request_device_code_raises_error_on_failure():
    """request_device_code should raise TidalAPIError on HTTP error"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        json={"error": "invalid_client"},
        status=400,
    )

    config = Config(client_id="bad_client", client_secret="bad_secret")
    session = TidalSession(config)

    try:
        session.request_device_code()
        assert False, "Should have raised TidalAPIError"
    except TidalAPIError as e:
        assert "400" in str(e)
