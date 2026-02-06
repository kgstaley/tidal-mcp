"""Authentication MCP tools."""

import logging

import requests
from server import mcp
from utils import DEFAULT_TIMEOUT, FLASK_APP_URL, http

logger = logging.getLogger(__name__)


@mcp.tool()
def tidal_login() -> dict:
    """
    Authenticate with TIDAL through browser login flow.
    This will open a browser window for the user to log in to their TIDAL account.

    Returns:
        A dictionary containing authentication status and user information if successful
    """
    try:
        response = http.get(f"{FLASK_APP_URL}/api/auth/login", timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            return {
                "status": "error",
                "message": f"Authentication failed: {error_data.get('message', 'Unknown error')}",
            }
    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL authentication service", exc_info=True)
        return {"status": "error", "message": f"Failed to connect to TIDAL authentication service: {e}"}
