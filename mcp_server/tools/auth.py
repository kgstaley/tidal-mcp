"""Authentication MCP tools."""

import logging
import time

import requests
from mcp_app import mcp
from utils import DEFAULT_TIMEOUT, FLASK_APP_URL, http

logger = logging.getLogger(__name__)

PKCE_POLL_INTERVAL = 2
PKCE_POLL_TIMEOUT = 120


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

        if response.status_code != 200:
            error_data = response.json()
            return {
                "status": "error",
                "message": f"Authentication failed: {error_data.get('message', 'Unknown error')}",
            }

        data = response.json()

        if data.get("status") == "pending":
            return _poll_for_auth_completion()

        return data

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL authentication service", exc_info=True)
        return {"status": "error", "message": f"Failed to connect to TIDAL authentication service: {e}"}


def _poll_for_auth_completion() -> dict:
    """Poll /api/auth/status until authentication completes or times out."""
    deadline = time.monotonic() + PKCE_POLL_TIMEOUT

    while time.monotonic() < deadline:
        time.sleep(PKCE_POLL_INTERVAL)
        try:
            status_resp = http.get(f"{FLASK_APP_URL}/api/auth/status", timeout=DEFAULT_TIMEOUT)
            status_data = status_resp.json()

            if status_data.get("authenticated"):
                return {
                    "status": "success",
                    "message": "Successfully authenticated with TIDAL",
                    "user": status_data.get("user"),
                }
        except requests.RequestException:
            logger.debug("Poll attempt failed, retrying...")

    return {"status": "error", "message": "Authentication timed out waiting for browser login."}
