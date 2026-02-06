"""Discovery and browsing routes for TIDAL API."""

import logging

import tidalapi
from flask import Blueprint, jsonify
from tidalapi.page import Page

from tidal_api.utils import (
    format_genre_data,
    handle_endpoint_errors,
    requires_tidal_auth,
    safe_attr,
    serialize_page_categories,
)

logger = logging.getLogger(__name__)

discovery_bp = Blueprint("discovery", __name__)

# Map URL content_type strings to tidalapi model classes
GENRE_CONTENT_TYPE_MAP = {
    "playlists": tidalapi.Playlist,
    "artists": tidalapi.Artist,
    "albums": tidalapi.Album,
    "tracks": tidalapi.Track,
    "videos": tidalapi.Video,
}

# Map content_type to Genre boolean attribute name
GENRE_HAS_ATTR_MAP = {
    "playlists": "playlists",
    "artists": "artists",
    "albums": "albums",
    "tracks": "tracks",
    "videos": "videos",
}


def _serialize_page_response(page) -> dict:
    """Build a standard response dict from a Page object."""
    categories = serialize_page_categories(page)
    return {
        "page_title": safe_attr(page, "title", ""),
        "categories": categories,
        "category_count": len(categories),
    }


@discovery_bp.route("/api/discover/for-you", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching For You page")
def get_for_you(session):
    """Get personalized For You recommendations."""
    page = session.for_you()
    return jsonify(_serialize_page_response(page))


@discovery_bp.route("/api/discover/explore", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching Explore page")
def get_explore(session):
    """Get editorial/trending Explore content."""
    page = session.explore()
    return jsonify(_serialize_page_response(page))


@discovery_bp.route("/api/discover/moods", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching moods")
def get_moods(session):
    """Get list of browsable moods."""
    page = session.moods()
    # Moods page has categories whose items are PageLinks
    categories = safe_attr(page, "categories") or []
    moods = []
    for category in categories:
        items = safe_attr(category, "items") or []
        for item in items:
            # PageLink items have title, api_path, icon, image_id
            if hasattr(item, "api_path"):
                moods.append(
                    {
                        "title": safe_attr(item, "title", ""),
                        "api_path": safe_attr(item, "api_path", ""),
                        "image_id": safe_attr(item, "image_id", ""),
                    }
                )
    return jsonify({"moods": moods, "count": len(moods)})


@discovery_bp.route("/api/discover/moods/<path:api_path>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("browsing mood")
def browse_mood(api_path: str, session):
    """Browse a specific mood's content by api_path."""
    page = Page(session, "")
    page = page.get(api_path)
    return jsonify(_serialize_page_response(page))


@discovery_bp.route("/api/discover/genres", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching genres")
def get_genres(session):
    """Get list of available genres."""
    genres = session.genre.get_genres()
    formatted = [format_genre_data(g) for g in genres]
    return jsonify({"genres": formatted, "count": len(formatted)})


@discovery_bp.route("/api/discover/genres/<genre_path>/<content_type>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("browsing genre content")
def browse_genre(genre_path: str, content_type: str, session):
    """Browse a genre's content by type (playlists, artists, albums, tracks, videos)."""
    if content_type not in GENRE_CONTENT_TYPE_MAP:
        valid = ", ".join(sorted(GENRE_CONTENT_TYPE_MAP.keys()))
        return jsonify({"error": f"Invalid content_type '{content_type}'. Must be one of: {valid}"}), 400

    genres = session.genre.get_genres()
    genre = next((g for g in genres if g.path == genre_path), None)
    if not genre:
        return jsonify({"error": f"Genre '{genre_path}' not found"}), 404

    has_attr = GENRE_HAS_ATTR_MAP[content_type]
    if not getattr(genre, has_attr, False):
        return jsonify({"error": f"Genre '{genre_path}' does not have {content_type}"}), 400

    model_class = GENRE_CONTENT_TYPE_MAP[content_type]
    try:
        items = genre.items(model_class)
    except TypeError as e:
        logger.warning("Genre '%s' does not support content type '%s': %s", genre_path, content_type, e)
        return jsonify({"error": f"Genre '{genre_path}' does not support {content_type}"}), 400

    # Format items using the same type-detection pattern
    from tidal_api.utils import _format_page_category_item

    formatted = []
    for item in items:
        result = _format_page_category_item(item)
        if result:
            formatted.append(result["data"])

    return jsonify(
        {
            "genre": genre_path,
            "content_type": content_type,
            "items": formatted,
            "count": len(formatted),
        }
    )
