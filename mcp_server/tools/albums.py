"""Album and track detail MCP tools."""

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
def get_album_info(album_id: str) -> dict:
    """
    Get detailed information about a TIDAL album including review, audio quality, and more.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Tell me about [album name]"
    - "Get info on [album]"
    - "What's this album about?"

    The user must be authenticated with TIDAL first.

    Args:
        album_id: The TIDAL album ID (required)

    Returns:
        A dictionary containing album details: name, artist, tracks, review, audio quality, and TIDAL URL
    """
    auth_error = check_tidal_auth("get album info")
    if auth_error:
        return auth_error

    id_error = validate_string(album_id, "album ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(f"/api/albums/{album_id}", "album", resource_id=album_id)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch album info", exc_info=True)
        return error_response(f"Failed to fetch album info: {e}")


@mcp.tool()
def get_album_tracks(album_id: str, limit: int = 50) -> dict:
    """
    Get the tracks on a TIDAL album.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What tracks are on [album]?"
    - "Show me the tracklist for [album]"
    - "List songs on [album]"

    Args:
        album_id: The TIDAL album ID (required)
        limit: Maximum number of tracks to return (default: 50)

    Returns:
        A dictionary containing the album's tracks
    """
    auth_error = check_tidal_auth("get album tracks")
    if auth_error:
        return auth_error

    id_error = validate_string(album_id, "album ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/albums/{album_id}/tracks",
            "album",
            params={"limit": limit},
            resource_id=album_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch album tracks", exc_info=True)
        return error_response(f"Failed to fetch album tracks: {e}")


@mcp.tool()
def get_similar_albums(album_id: str) -> dict:
    """
    Get albums similar to a given TIDAL album.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Find albums like [album]"
    - "What's similar to [album]?"
    - "Recommend albums like [album]"

    Args:
        album_id: The TIDAL album ID (required)

    Returns:
        A dictionary containing similar albums
    """
    auth_error = check_tidal_auth("get similar albums")
    if auth_error:
        return auth_error

    id_error = validate_string(album_id, "album ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/albums/{album_id}/similar",
            "album",
            resource_id=album_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch similar albums", exc_info=True)
        return error_response(f"Failed to fetch similar albums: {e}")


@mcp.tool()
def get_album_review(album_id: str) -> dict:
    """
    Get the editorial review for a TIDAL album.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What's the review for [album]?"
    - "Is [album] any good?"
    - "Get the album review"

    Note: Not all albums have reviews available.

    Args:
        album_id: The TIDAL album ID (required)

    Returns:
        A dictionary containing the album review text
    """
    auth_error = check_tidal_auth("get album review")
    if auth_error:
        return auth_error

    id_error = validate_string(album_id, "album ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/albums/{album_id}/review",
            "album",
            resource_id=album_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch album review", exc_info=True)
        return error_response(f"Failed to fetch album review: {e}")


@mcp.tool()
def get_track_info(track_id: str) -> dict:
    """
    Get detailed information about a TIDAL track including audio quality, ISRC, and more.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Tell me about [track name]"
    - "Get info on [song]"
    - "What quality is [track] available in?"

    The user must be authenticated with TIDAL first.

    Args:
        track_id: The TIDAL track ID (required)

    Returns:
        A dictionary containing track details: title, artist, album, audio quality, ISRC, and TIDAL URL
    """
    auth_error = check_tidal_auth("get track info")
    if auth_error:
        return auth_error

    id_error = validate_string(track_id, "track ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(f"/api/tracks/{track_id}", "track", resource_id=track_id)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch track info", exc_info=True)
        return error_response(f"Failed to fetch track info: {e}")


@mcp.tool()
def get_track_lyrics(track_id: str) -> dict:
    """
    Get the lyrics for a TIDAL track.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me the lyrics for [song]"
    - "What are the words to [track]?"
    - "Get lyrics for [song]"

    Note: Not all tracks have lyrics available.

    Args:
        track_id: The TIDAL track ID (required)

    Returns:
        A dictionary containing lyrics text, synced subtitles, and provider
    """
    auth_error = check_tidal_auth("get track lyrics")
    if auth_error:
        return auth_error

    id_error = validate_string(track_id, "track ID")
    if id_error:
        return id_error

    try:
        data = mcp_get(
            f"/api/tracks/{track_id}/lyrics",
            "track",
            resource_id=track_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch track lyrics", exc_info=True)
        return error_response(f"Failed to fetch track lyrics: {e}")
