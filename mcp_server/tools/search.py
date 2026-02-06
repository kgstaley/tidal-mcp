"""Search MCP tools."""

import requests
from server import mcp
from utils import (
    FLASK_APP_URL,
    check_tidal_auth,
    error_response,
    handle_api_response,
    validate_string,
)


@mcp.tool()
def search_tidal(query: str, types: list[str] | None = None, limit: int = 20) -> dict:
    """
    Search TIDAL catalog for artists, tracks, albums, playlists, and videos.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Search for [artist name]"
    - "Find songs by [artist]"
    - "Look up [album name]"
    - "Search TIDAL for [query]"
    - "Find [track name]"
    - Any request to search for music, artists, albums, or playlists

    This function searches the TIDAL catalog and returns matching results.
    The user must be authenticated with TIDAL first.

    When processing the results of this tool:
    1. Present results organized by type (artists, tracks, albums, etc.)
    2. Highlight the top_hit if available as the most relevant result
    3. Include TIDAL URLs for easy access
    4. If searching for specific content, focus on the most relevant matches

    Args:
        query: Search query string (required)
        types: Optional list of content types to search. Valid values:
               ["artists", "tracks", "albums", "playlists", "videos"]
               If not provided, searches all types.
        limit: Maximum results per type (default: 20, max: 50)

    Returns:
        A dictionary containing search results organized by type, with a top_hit if available
    """
    auth_error = check_tidal_auth("search TIDAL")
    if auth_error:
        return auth_error

    query_error = validate_string(query, "search query")
    if query_error:
        return query_error

    try:
        params = {"query": query, "limit": limit}
        if types:
            params["types"] = ",".join(types)

        response = requests.get(f"{FLASK_APP_URL}/api/search", params=params)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "query": query,
                "top_hit": data.get("top_hit"),
                "artists": data.get("artists", []),
                "tracks": data.get("tracks", []),
                "albums": data.get("albums", []),
                "playlists": data.get("playlists", []),
                "videos": data.get("videos", []),
            }

        api_error = handle_api_response(response, "search")
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL search service: {str(e)}")
