"""Artist MCP tools."""

import logging

import requests
from mcp_app import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_get,
    validate_string,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_artist_info(artist_id: str) -> dict:
    """
    Get detailed information about a TIDAL artist including bio and roles.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Tell me about [artist name]"
    - "Who is [artist name]?"
    - "Get info on [artist]"
    - "What do you know about [artist] on TIDAL?"

    The user must be authenticated with TIDAL first.

    Args:
        artist_id: The TIDAL artist ID (required)

    Returns:
        A dictionary containing artist details: name, bio, roles, picture URL, and TIDAL URL
    """
    auth_error = check_tidal_auth("get artist info")
    if auth_error:
        return auth_error

    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(f"/api/artists/{artist_id}", "artist", resource_id=artist_id)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch artist info", exc_info=True)
        return error_response(f"Failed to fetch artist info: {e}")


@mcp.tool()
def get_artist_top_tracks(artist_id: str, limit: int = 20) -> dict:
    """
    Get an artist's top/most popular tracks on TIDAL.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What are [artist]'s top songs?"
    - "Show me [artist]'s most popular tracks"
    - "Play [artist]'s hits"

    Args:
        artist_id: The TIDAL artist ID (required)
        limit: Maximum number of tracks to return (default: 20)

    Returns:
        A dictionary containing the artist's top tracks
    """
    auth_error = check_tidal_auth("get artist top tracks")
    if auth_error:
        return auth_error

    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/artists/{artist_id}/top-tracks",
            "artist",
            params={"limit": limit},
            resource_id=artist_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch artist top tracks", exc_info=True)
        return error_response(f"Failed to fetch artist top tracks: {e}")


@mcp.tool()
def get_artist_albums(artist_id: str, filter: str = "albums", limit: int = 50) -> dict:
    """
    Get an artist's albums, EPs/singles, or other releases on TIDAL.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me [artist]'s albums"
    - "What albums does [artist] have?"
    - "List [artist]'s EPs and singles"
    - "Show me [artist]'s discography"

    Args:
        artist_id: The TIDAL artist ID (required)
        filter: Type of releases — "albums", "ep_singles", or "other" (default: "albums")
        limit: Maximum number of albums to return (default: 50)

    Returns:
        A dictionary containing the artist's albums/releases
    """
    auth_error = check_tidal_auth("get artist albums")
    if auth_error:
        return auth_error

    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/artists/{artist_id}/albums",
            "artist",
            params={"filter": filter, "limit": limit},
            resource_id=artist_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch artist albums", exc_info=True)
        return error_response(f"Failed to fetch artist albums: {e}")


@mcp.tool()
def get_similar_artists(artist_id: str) -> dict:
    """
    Get artists similar to a given TIDAL artist.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Who is similar to [artist]?"
    - "Find artists like [artist]"
    - "Recommend artists similar to [artist]"

    Args:
        artist_id: The TIDAL artist ID (required)

    Returns:
        A dictionary containing similar artists
    """
    auth_error = check_tidal_auth("get similar artists")
    if auth_error:
        return auth_error

    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/artists/{artist_id}/similar",
            "artist",
            resource_id=artist_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch similar artists", exc_info=True)
        return error_response(f"Failed to fetch similar artists: {e}")


@mcp.tool()
def get_artist_radio(artist_id: str, limit: int = 50) -> dict:
    """
    Get a radio mix of tracks based on a TIDAL artist.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Play [artist] radio"
    - "Create a mix based on [artist]"
    - "Give me tracks inspired by [artist]"

    Note: TIDAL returns up to 100 radio tracks. The limit parameter
    truncates the result if you want fewer.

    Args:
        artist_id: The TIDAL artist ID (required)
        limit: Maximum number of tracks to return (default: 50, max: 100)

    Returns:
        A dictionary containing radio tracks based on the artist
    """
    auth_error = check_tidal_auth("get artist radio")
    if auth_error:
        return auth_error

    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/artists/{artist_id}/radio",
            "artist",
            params={"limit": limit},
            resource_id=artist_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch artist radio", exc_info=True)
        return error_response(f"Failed to fetch artist radio: {e}")
