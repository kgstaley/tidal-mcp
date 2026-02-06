"""Authentication MCP tools."""

import requests
from server import mcp
from utils import FLASK_APP_URL


@mcp.tool()
def tidal_login() -> dict:
    """
    Authenticate with TIDAL through browser login flow.
    This will open a browser window for the user to log in to their TIDAL account.

    Returns:
        A dictionary containing authentication status and user information if successful
    """
    try:
        response = requests.get(f"{FLASK_APP_URL}/api/auth/login")

        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            return {
                "status": "error",
                "message": f"Authentication failed: {error_data.get('message', 'Unknown error')}",
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to TIDAL authentication service: {str(e)}"}
