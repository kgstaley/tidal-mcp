"""Favorites CRUD routes for TIDAL API."""

import logging

from flask import Blueprint, jsonify, request

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import (
    bound_limit,
    fetch_all_paginated,
    format_album_data,
    format_artist_data,
    format_mix_data,
    format_playlist_search_data,
    format_track_data,
    format_video_data,
    handle_endpoint_errors,
    require_json_body,
    requires_tidal_auth,
)

logger = logging.getLogger(__name__)

favorites_bp = Blueprint("favorites", __name__)

VALID_TYPES = {"artists", "albums", "tracks", "videos", "playlists", "mixes"}
READ_ONLY_TYPES = {"mixes"}

# (favorites_method_name, formatter, paginated?)
GET_DISPATCH = {
    "artists": ("artists", format_artist_data, True),
    "albums": ("albums", format_album_data, True),
    "tracks": ("tracks", format_track_data, True),
    "videos": ("videos", format_video_data, False),
    "playlists": ("playlists", format_playlist_search_data, True),
    "mixes": ("mixes", format_mix_data, True),
}

ADD_DISPATCH = {
    "artists": "add_artist",
    "albums": "add_album",
    "tracks": "add_track",
    "videos": "add_video",
    "playlists": "add_playlist",
}

REMOVE_DISPATCH = {
    "artists": "remove_artist",
    "albums": "remove_album",
    "tracks": "remove_track",
    "videos": "remove_video",
    "playlists": "remove_playlist",
}


@favorites_bp.route("/api/favorites/<fav_type>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching favorites")
def get_favorites(fav_type: str, session: BrowserSession):
    if fav_type not in VALID_TYPES:
        return jsonify({"error": f"Invalid type '{fav_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}"}), 400

    favorites = session.user.favorites
    limit = bound_limit(request.args.get("limit", default=50, type=int))

    method_name, formatter, paginated = GET_DISPATCH[fav_type]

    if fav_type == "tracks":
        order = request.args.get("order", "DATE")
        order_direction = request.args.get("order_direction", "DESC")
        items = fetch_all_paginated(
            lambda limit, offset: favorites.tracks(
                limit=limit, offset=offset, order=order, order_direction=order_direction
            ),
            limit=limit,
        )
    elif paginated:
        items = fetch_all_paginated(getattr(favorites, method_name), limit=limit)
    else:
        # videos: no pagination params
        all_items = getattr(favorites, method_name)()
        items = all_items[:limit]

    formatted = [formatter(item) for item in items]
    return jsonify({"type": fav_type, "items": formatted, "total": len(formatted)})


@favorites_bp.route("/api/favorites/<fav_type>", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("adding favorite")
def add_favorite(fav_type: str, session: BrowserSession):
    if fav_type not in VALID_TYPES:
        return jsonify({"error": f"Invalid type '{fav_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}"}), 400

    if fav_type in READ_ONLY_TYPES:
        return jsonify({"error": f"Cannot add favorites of type '{fav_type}'"}), 400

    data, error = require_json_body(["id"])
    if error:
        return error

    favorites = session.user.favorites
    item_id = str(data["id"])
    add_method = getattr(favorites, ADD_DISPATCH[fav_type])
    success = add_method(item_id)

    if success:
        return jsonify({"status": "success", "type": fav_type, "id": item_id})
    return jsonify({"error": f"Failed to add {fav_type} favorite"}), 500


@favorites_bp.route("/api/favorites/<fav_type>", methods=["DELETE"])
@requires_tidal_auth
@handle_endpoint_errors("removing favorite")
def remove_favorite(fav_type: str, session: BrowserSession):
    if fav_type not in VALID_TYPES:
        return jsonify({"error": f"Invalid type '{fav_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}"}), 400

    if fav_type in READ_ONLY_TYPES:
        return jsonify({"error": f"Cannot remove favorites of type '{fav_type}'"}), 400

    data, error = require_json_body(["id"])
    if error:
        return error

    favorites = session.user.favorites
    item_id = str(data["id"])
    remove_method = getattr(favorites, REMOVE_DISPATCH[fav_type])
    success = remove_method(item_id)

    if success:
        return jsonify({"status": "success", "type": fav_type, "id": item_id})
    return jsonify({"error": f"Failed to remove {fav_type} favorite"}), 500
