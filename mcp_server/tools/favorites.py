"""Favorites CRUD MCP tools."""

import logging

import requests
from mcp_app import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_delete,
    mcp_get,
    mcp_post,
    validate_string,
)

logger = logging.getLogger(__name__)

VALID_TYPES = {"artists", "albums", "tracks", "videos", "playlists", "mixes"}
READ_ONLY_TYPES = {"mixes"}


@mcp.tool()
def get_favorites(type: str, limit: int = 50, order: str = "DATE", order_direction: str = "DESC") -> dict:
    """
    Get the user's TIDAL favorites by content type.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Show me my favorite artists/albums/tracks/videos/playlists/mixes"
    - "What artists have I saved?"
    - "List my favorite albums"

    Args:
        type: Content type — one of: artists, albums, tracks, videos, playlists, mixes
        limit: Maximum number of items to return (default: 50, max: 5000)
        order: Sort order for tracks — "DATE" or "NAME" (default: "DATE")
        order_direction: Sort direction for tracks — "ASC" or "DESC" (default: "DESC")

    Returns:
        A dictionary containing the favorite items of the requested type.
    """
    auth_error = check_tidal_auth("fetch your favorites")
    if auth_error:
        return auth_error

    type_error = validate_string(type, "type")
    if type_error:
        return type_error

    if type not in VALID_TYPES:
        return error_response(f"Invalid type '{type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}")

    try:
        params = {"limit": limit}
        if type == "tracks":
            params["order"] = order
            params["order_direction"] = order_direction

        return mcp_get(f"/api/favorites/{type}", "favorites", params=params)

    except requests.RequestException as e:
        logger.error("Failed to fetch favorites", exc_info=True)
        return error_response(f"Failed to fetch favorites: {e}")


@mcp.tool()
def add_favorite(type: str, id: str) -> dict:
    """
    Add an item to the user's TIDAL favorites.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Add this artist/album/track to my favorites"
    - "Save this song"
    - "Favorite this album"

    Args:
        type: Content type — one of: artists, albums, tracks, videos, playlists
        id: The TIDAL ID of the item to add

    Returns:
        A dictionary confirming the item was added.
    """
    auth_error = check_tidal_auth("add to your favorites")
    if auth_error:
        return auth_error

    type_error = validate_string(type, "type")
    if type_error:
        return type_error

    if type not in VALID_TYPES:
        return error_response(f"Invalid type '{type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}")

    if type in READ_ONLY_TYPES:
        return error_response(f"Cannot add favorites of type '{type}'")

    id_error = validate_string(id, "id")
    if id_error:
        return id_error

    try:
        return mcp_post(f"/api/favorites/{type}", "favorites", payload={"id": id})

    except requests.RequestException as e:
        logger.error("Failed to add favorite", exc_info=True)
        return error_response(f"Failed to add favorite: {e}")


@mcp.tool()
def remove_favorite(type: str, id: str) -> dict:
    """
    Remove an item from the user's TIDAL favorites.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Remove this artist/album/track from my favorites"
    - "Unfavorite this song"
    - "Delete this from my saved music"

    Args:
        type: Content type — one of: artists, albums, tracks, videos, playlists
        id: The TIDAL ID of the item to remove

    Returns:
        A dictionary confirming the item was removed.
    """
    auth_error = check_tidal_auth("remove from your favorites")
    if auth_error:
        return auth_error

    type_error = validate_string(type, "type")
    if type_error:
        return type_error

    if type not in VALID_TYPES:
        return error_response(f"Invalid type '{type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}")

    if type in READ_ONLY_TYPES:
        return error_response(f"Cannot remove favorites of type '{type}'")

    id_error = validate_string(id, "id")
    if id_error:
        return id_error

    try:
        return mcp_delete(f"/api/favorites/{type}", "favorites", payload={"id": id})

    except requests.RequestException as e:
        logger.error("Failed to remove favorite", exc_info=True)
        return error_response(f"Failed to remove favorite: {e}")
