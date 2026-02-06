"""Discovery and browsing MCP tools."""

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

VALID_GENRE_CONTENT_TYPES = {"playlists", "artists", "albums", "tracks", "videos"}


@mcp.tool()
def get_for_you_page() -> dict:
    """
    Get your personalized TIDAL "For You" recommendations.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What should I listen to?"
    - "Show me my recommendations"
    - "What's recommended for me?"
    - "Personalized music suggestions"

    The user must be authenticated with TIDAL first.

    Returns:
        A dictionary containing personalized recommendation categories with albums, playlists, mixes, etc.
    """
    auth_error = check_tidal_auth("get personalized recommendations")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/discover/for-you", "For You page")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch For You page", exc_info=True)
        return error_response(f"Failed to fetch For You page: {e}")


@mcp.tool()
def explore_tidal() -> dict:
    """
    Browse TIDAL's editorial and trending content.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What's new on TIDAL?"
    - "Show me trending music"
    - "What's popular right now?"
    - "Browse new releases"

    The user must be authenticated with TIDAL first.

    Returns:
        A dictionary containing editorial/trending categories with albums, tracks, playlists, etc.
    """
    auth_error = check_tidal_auth("explore TIDAL content")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/discover/explore", "Explore page")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch Explore page", exc_info=True)
        return error_response(f"Failed to fetch Explore page: {e}")


@mcp.tool()
def get_tidal_moods() -> dict:
    """
    Get the list of available moods on TIDAL (e.g., Chill, Party, Workout).

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What moods are available?"
    - "Show me mood categories"
    - "I want something chill" (list moods first, then browse)
    - "What vibes can I browse?"

    The user must be authenticated with TIDAL first.

    Returns:
        A dictionary containing available moods with titles and API paths for browsing
    """
    auth_error = check_tidal_auth("get moods")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/discover/moods", "moods")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch moods", exc_info=True)
        return error_response(f"Failed to fetch moods: {e}")


@mcp.tool()
def browse_tidal_mood(api_path: str) -> dict:
    """
    Browse a specific mood's content on TIDAL.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me chill music"
    - "Browse the party mood"
    - "What's in the workout category?"

    Use get_tidal_moods() first to get the available moods and their api_path values.

    The user must be authenticated with TIDAL first.

    Args:
        api_path: The API path from the moods list (e.g., "pages/moods_chill")

    Returns:
        A dictionary containing the mood's content categories with playlists, albums, etc.
    """
    auth_error = check_tidal_auth("browse mood")
    if auth_error:
        return auth_error

    path_error = validate_string(api_path, "mood API path")
    if path_error:
        return path_error

    try:
        data = mcp_get(f"/api/discover/moods/{api_path}", "mood page")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to browse mood", exc_info=True)
        return error_response(f"Failed to browse mood: {e}")


@mcp.tool()
def get_tidal_genres() -> dict:
    """
    Get the list of available music genres on TIDAL.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "What genres are available?"
    - "Show me genre categories"
    - "What genres can I browse?"
    - "List music genres"

    The user must be authenticated with TIDAL first.

    Returns:
        A dictionary containing available genres with names, paths, and supported content types
    """
    auth_error = check_tidal_auth("get genres")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/discover/genres", "genres")
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch genres", exc_info=True)
        return error_response(f"Failed to fetch genres: {e}")


@mcp.tool()
def browse_tidal_genre(genre_path: str, content_type: str = "playlists") -> dict:
    """
    Browse a genre's content on TIDAL by content type.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me pop albums"
    - "What rock playlists are there?"
    - "Browse jazz artists"
    - "Find hip-hop tracks"

    Use get_tidal_genres() first to get available genres and their paths.

    The user must be authenticated with TIDAL first.

    Args:
        genre_path: The genre path from the genres list (e.g., "pop", "rock", "jazz")
        content_type: Type of content: "playlists", "artists", "albums", "tracks", or "videos" (default: "playlists")

    Returns:
        A dictionary containing the genre's content items (albums, playlists, artists, etc.)
    """
    auth_error = check_tidal_auth("browse genre")
    if auth_error:
        return auth_error

    path_error = validate_string(genre_path, "genre path")
    if path_error:
        return path_error

    if content_type not in VALID_GENRE_CONTENT_TYPES:
        valid = ", ".join(sorted(VALID_GENRE_CONTENT_TYPES))
        return error_response(f"Invalid content_type '{content_type}'. Must be one of: {valid}")

    try:
        data = mcp_get(f"/api/discover/genres/{genre_path}/{content_type}", "genre content", resource_id=genre_path)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to browse genre", exc_info=True)
        return error_response(f"Failed to browse genre: {e}")
