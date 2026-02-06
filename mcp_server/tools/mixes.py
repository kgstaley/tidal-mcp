"""Mix MCP tools."""

import logging

import requests
from server import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_get,
    validate_string,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_user_mixes() -> dict:
    """
    Get the user's personalized TIDAL mixes (daily mixes, discovery, etc.).

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me my mixes"
    - "What mixes do I have?"
    - "Get my daily mixes"
    - "Show my personalized playlists"

    The user must be authenticated with TIDAL first.

    Returns:
        A dictionary containing the user's mixes with titles, types, and images
    """
    auth_error = check_tidal_auth("get user mixes")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/mixes", "user mixes")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch user mixes", exc_info=True)
        return error_response(f"Failed to fetch user mixes: {e}")


@mcp.tool()
def get_mix_tracks(mix_id: str, limit: int = 50) -> dict:
    """
    Get the tracks in a specific TIDAL mix.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me tracks in this mix"
    - "What's in mix [id]?"
    - "Get tracks from [mix name]"
    - "Play this mix"

    The user must be authenticated with TIDAL first.

    Args:
        mix_id: The TIDAL mix ID (required)
        limit: Maximum number of tracks to return (default: 50, max: 5000)

    Returns:
        A dictionary containing tracks from the mix with artist, album, and duration info
    """
    auth_error = check_tidal_auth("get mix tracks")
    if auth_error:
        return auth_error

    id_error = validate_string(mix_id, "mix ID")
    if id_error:
        return id_error

    try:
        params = {"limit": limit}
        data = mcp_get(f"/api/mixes/{mix_id}/tracks", "mix tracks", params=params, resource_id=mix_id)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch mix tracks", exc_info=True)
        return error_response(f"Failed to fetch mix tracks: {e}")
