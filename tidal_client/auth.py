"""OAuth 2.0 Device Code Flow for TIDAL authentication"""
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
