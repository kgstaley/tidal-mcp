"""OAuth 2.0 Device Code Flow for TIDAL authentication"""
import time
from typing import Dict, Any
import requests

from tidal_client.config import Config
from tidal_client.exceptions import AuthenticationError

# OAuth scopes for TIDAL API
OAUTH_SCOPES = "r_usr+w_usr+w_sub"


def request_device_code(config: Config) -> Dict[str, Any]:
    """Request device code from TIDAL OAuth server

    Args:
        config: TIDAL API configuration with client_id

    Returns:
        Dict with device_code, user_code, verification_uri, expires_in, interval

    Raises:
        AuthenticationError: If device code request fails
    """
    try:
        response = requests.post(
            config.device_auth_url,
            data={
                "client_id": config.client_id,
                "scope": OAUTH_SCOPES
            },
            timeout=config.default_timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AuthenticationError(f"Failed to request device code: {e}") from e


def poll_for_token(
    config: Config,
    device_code: str,
    interval: int = 5,
    expires_in: int = 300
) -> Dict[str, Any]:
    """Poll TIDAL OAuth server for access token

    Args:
        config: TIDAL API configuration
        device_code: Device code from request_device_code()
        interval: Seconds to wait between polls (default 5)
        expires_in: Seconds before device code expires (default 300)

    Returns:
        Dict with access_token, refresh_token, expires_in, user_id

    Raises:
        AuthenticationError: If polling fails or times out
    """
    start_time = time.time()

    while True:
        # Check if device code expired
        if time.time() - start_time > expires_in:
            raise AuthenticationError("Device code expired - user did not authorize in time")

        try:
            response = requests.post(
                config.auth_token_url,
                data={
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "scope": OAUTH_SCOPES
                },
                timeout=config.default_timeout
            )

            data = response.json()

            # Check for authorization_pending
            if "error" in data:
                if data["error"] == "authorization_pending":
                    # User hasn't authorized yet, keep polling
                    time.sleep(interval)
                    continue
                else:
                    # Other error (expired_token, access_denied, etc.)
                    raise AuthenticationError(f"OAuth error: {data['error']}")

            # Success - return token data
            response.raise_for_status()
            return data

        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to poll for token: {e}") from e
