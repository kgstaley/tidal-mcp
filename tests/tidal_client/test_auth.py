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


@responses.activate
def test_poll_for_token_returns_tokens_on_success():
    """poll_for_token should return access and refresh tokens when authorized"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {"user_id": "12345"},
        },
        status=200,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)

    result = session.poll_for_token(device_code="test_device_code", interval=1, timeout=5)

    assert result["access_token"] == "new_access_token"
    assert result["refresh_token"] == "new_refresh_token"
    assert result["expires_in"] == 3600
    assert session._access_token == "new_access_token"
    assert session._refresh_token == "new_refresh_token"
    assert session._user_id == "12345"
    assert session._token_expires_at is not None


@responses.activate
def test_poll_for_token_retries_on_authorization_pending():
    """poll_for_token should retry when authorization is pending"""
    # First two requests return "authorization_pending"
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "authorization_pending"},
        status=400,
    )
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "authorization_pending"},
        status=400,
    )
    # Third request succeeds
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "success_token",
            "refresh_token": "success_refresh",
            "expires_in": 3600,
            "user": {"user_id": "67890"},
        },
        status=200,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)

    result = session.poll_for_token(device_code="test_device_code", interval=0.1, timeout=5)

    # Should have made 3 requests
    assert len(responses.calls) == 3
    assert result["access_token"] == "success_token"


@responses.activate
def test_poll_for_token_raises_error_on_access_denied():
    """poll_for_token should raise TidalAPIError when user denies access"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "access_denied", "error_description": "User denied access"},
        status=400,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)

    try:
        session.poll_for_token(device_code="test_device_code", interval=1, timeout=5)
        assert False, "Should have raised TidalAPIError"
    except TidalAPIError as e:
        assert "access_denied" in str(e) or "denied" in str(e).lower()


@responses.activate
def test_poll_for_token_raises_error_on_expired_token():
    """poll_for_token should raise TidalAPIError when device code expires"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "expired_token"},
        status=400,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)

    try:
        session.poll_for_token(device_code="test_device_code", interval=1, timeout=5)
        assert False, "Should have raised TidalAPIError"
    except TidalAPIError as e:
        assert "expired" in str(e).lower()


@responses.activate
def test_poll_for_token_sends_correct_payload():
    """poll_for_token should send correct OAuth token request"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"access_token": "token", "refresh_token": "refresh", "expires_in": 3600},
        status=200,
    )

    config = Config(client_id="my_client", client_secret="my_secret")
    session = TidalSession(config)

    session.poll_for_token(device_code="my_device_code", interval=1, timeout=5)

    request = responses.calls[0].request
    body = request.body

    # URL-encoded format (colons become %3A)
    assert "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code" in body
    assert "device_code=my_device_code" in body
    assert "client_id=my_client" in body
    assert "client_secret=my_secret" in body


@responses.activate
def test_refresh_token_updates_access_token():
    """refresh_token should get new access token using refresh token"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={
            "access_token": "refreshed_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {"user_id": "12345"},
        },
        status=200,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)
    session._refresh_token = "old_refresh_token"
    session._user_id = "12345"

    result = session.refresh_access_token()

    assert result["access_token"] == "refreshed_access_token"
    assert result["refresh_token"] == "new_refresh_token"
    assert session._access_token == "refreshed_access_token"
    assert session._refresh_token == "new_refresh_token"
    assert session._token_expires_at is not None


@responses.activate
def test_refresh_token_sends_correct_payload():
    """refresh_token should send correct grant_type and tokens"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"access_token": "new_token", "refresh_token": "new_refresh", "expires_in": 3600},
        status=200,
    )

    config = Config(client_id="my_client", client_secret="my_secret")
    session = TidalSession(config)
    session._refresh_token = "my_refresh_token"

    session.refresh_access_token()

    request = responses.calls[0].request
    body = request.body

    assert "grant_type=refresh_token" in body
    assert "refresh_token=my_refresh_token" in body
    assert "client_id=my_client" in body
    assert "client_secret=my_secret" in body


@responses.activate
def test_refresh_token_raises_error_when_no_refresh_token():
    """refresh_token should raise error if no refresh token available"""
    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)
    # Don't set refresh_token

    try:
        session.refresh_access_token()
        assert False, "Should have raised TidalAPIError"
    except TidalAPIError as e:
        assert "refresh token" in str(e).lower()


@responses.activate
def test_refresh_token_raises_error_on_invalid_token():
    """refresh_token should raise error if refresh token is invalid"""
    responses.add(
        responses.POST,
        "https://auth.tidal.com/v1/oauth2/token",
        json={"error": "invalid_grant", "error_description": "Invalid refresh token"},
        status=400,
    )

    config = Config(client_id="test_client", client_secret="test_secret")
    session = TidalSession(config)
    session._refresh_token = "invalid_refresh_token"

    try:
        session.refresh_access_token()
        assert False, "Should have raised TidalAPIError"
    except TidalAPIError as e:
        assert "invalid" in str(e).lower() or "refresh" in str(e).lower()
