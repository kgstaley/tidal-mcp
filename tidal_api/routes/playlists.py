"""Playlist routes for TIDAL API."""

import logging

from flask import Blueprint, jsonify, request

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import (
    bound_limit,
    check_user_playlist,
    fetch_all_paginated,
    format_track_data,
    format_user_playlist_data,
    get_playlist_or_404,
    handle_endpoint_errors,
    require_json_body,
    requires_tidal_auth,
)

logger = logging.getLogger(__name__)

playlists_bp = Blueprint("playlists", __name__)


@playlists_bp.route("/api/playlists", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("creating playlist")
def create_playlist(session: BrowserSession):
    """
    Creates a new TIDAL playlist and adds tracks to it.

    Expected JSON payload:
    {
        "title": "Playlist title",
        "description": "Playlist description",
        "track_ids": [123456789, 987654321, ...]
    }

    Returns the created playlist information.
    """
    data, error = require_json_body(required_fields=["title", "track_ids"])
    if error:
        return error

    title = data["title"]
    track_ids = data["track_ids"]
    description = data.get("description", "")

    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    playlist = session.user.create_playlist(title, description)
    playlist.add(track_ids)
    playlist_info = format_user_playlist_data(playlist)

    return jsonify(
        {
            "status": "success",
            "message": f"Playlist '{title}' created successfully with {len(track_ids)} tracks",
            "playlist": playlist_info,
        }
    )


@playlists_bp.route("/api/playlists", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching playlists")
def get_user_playlists(session: BrowserSession):
    """
    Get the user's playlists from TIDAL.
    """
    playlists = session.user.playlists()

    playlist_list = [format_user_playlist_data(playlist) for playlist in playlists]

    sorted_playlists = sorted(playlist_list, key=lambda x: x.get("last_updated", ""), reverse=True)

    return jsonify({"playlists": sorted_playlists})


@playlists_bp.route("/api/playlists/<playlist_id>/tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching playlist tracks")
def get_playlist_tracks(playlist_id: str, session: BrowserSession):
    """
    Get tracks from a specific TIDAL playlist.
    """
    limit = bound_limit(request.args.get("limit", default=1000, type=int))

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    tracks = fetch_all_paginated(lambda lim, off: playlist.items(limit=lim, offset=off), limit=limit)

    track_list = [format_track_data(track) for track in tracks]

    return jsonify({"playlist_id": playlist.id, "tracks": track_list, "total_tracks": len(track_list)})


@playlists_bp.route("/api/playlists/<playlist_id>", methods=["DELETE"])
@requires_tidal_auth
@handle_endpoint_errors("deleting playlist")
def delete_playlist(playlist_id: str, session: BrowserSession):
    """
    Delete a TIDAL playlist by its ID.
    """
    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    playlist.delete()

    return jsonify({"status": "success", "message": f"Playlist with ID {playlist_id} was successfully deleted"})


@playlists_bp.route("/api/playlists/<playlist_id>/tracks", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("adding tracks to playlist")
def add_tracks_to_playlist(playlist_id: str, session: BrowserSession):
    """
    Add tracks to an existing TIDAL playlist.

    Expected JSON payload:
    {
        "track_ids": [123456789, 987654321, ...],
        "allow_duplicates": false,  // optional, default false
        "position": -1  // optional, -1 = append to end
    }
    """
    data, error = require_json_body(required_fields=["track_ids"])
    if error:
        return error

    track_ids = data["track_ids"]
    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    allow_duplicates = data.get("allow_duplicates", False)
    position = data.get("position", -1)

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "add")
    if error:
        return error

    if position == -1:
        added_indices = playlist.add(track_ids, allow_duplicates=allow_duplicates)
    else:
        added_indices = playlist.add(track_ids, allow_duplicates=allow_duplicates, position=position)

    return jsonify(
        {
            "status": "success",
            "message": f"Added {len(track_ids)} tracks to playlist",
            "playlist_id": playlist_id,
            "added_count": len(added_indices) if added_indices else len(track_ids),
        }
    )


@playlists_bp.route("/api/playlists/<playlist_id>/tracks", methods=["DELETE"])
@requires_tidal_auth
@handle_endpoint_errors("removing tracks from playlist")
def remove_tracks_from_playlist(playlist_id: str, session: BrowserSession):
    """
    Remove tracks from a TIDAL playlist.

    Expected JSON payload:
    {
        "track_ids": [123456789, 987654321, ...]
    }
    """
    data, error = require_json_body(required_fields=["track_ids"])
    if error:
        return error

    track_ids = data["track_ids"]
    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "remove")
    if error:
        return error

    removed_count = 0
    failed_track_ids = []
    for track_id in track_ids:
        try:
            playlist.remove_by_id(track_id)
            removed_count += 1
        except Exception:
            logger.warning("Failed to remove track %s from playlist %s", track_id, playlist_id, exc_info=True)
            failed_track_ids.append(track_id)

    result = {
        "status": "success",
        "message": f"Removed {removed_count} tracks from playlist",
        "playlist_id": playlist_id,
        "removed_count": removed_count,
    }

    if failed_track_ids:
        result["failed_track_ids"] = failed_track_ids

    return jsonify(result)


@playlists_bp.route("/api/playlists/<playlist_id>", methods=["PATCH"])
@requires_tidal_auth
@handle_endpoint_errors("editing playlist")
def edit_playlist(playlist_id: str, session: BrowserSession):
    """
    Edit a TIDAL playlist's metadata (title and/or description).

    Expected JSON payload:
    {
        "title": "New Title",        // optional
        "description": "New desc"    // optional (at least one required)
    }
    """
    data, error = require_json_body()
    if error:
        return error

    title = data.get("title")
    description = data.get("description")

    if title is None and description is None:
        return jsonify({"error": "At least one of 'title' or 'description' must be provided"}), 400

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "edit")
    if error:
        return error

    playlist.edit(title=title, description=description)

    # Re-fetch playlist to get updated data
    playlist = session.playlist(playlist_id)
    playlist_info = format_user_playlist_data(playlist)

    return jsonify({"status": "success", "message": "Playlist updated successfully", "playlist": playlist_info})


@playlists_bp.route("/api/playlists/<playlist_id>/visibility/public", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("setting playlist public")
def set_playlist_public(playlist_id: str, session: BrowserSession):
    """
    Make a TIDAL playlist public.
    """
    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "visibility")
    if error:
        return error

    playlist.set_playlist_public()

    return jsonify(
        {"status": "success", "message": "Playlist is now public", "playlist_id": playlist_id, "public": True}
    )


@playlists_bp.route("/api/playlists/<playlist_id>/visibility/private", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("setting playlist private")
def set_playlist_private(playlist_id: str, session: BrowserSession):
    """
    Make a TIDAL playlist private.
    """
    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "visibility")
    if error:
        return error

    playlist.set_playlist_private()

    return jsonify(
        {"status": "success", "message": "Playlist is now private", "playlist_id": playlist_id, "public": False}
    )


@playlists_bp.route("/api/playlists/<playlist_id>/tracks/all", methods=["DELETE"])
@requires_tidal_auth
@handle_endpoint_errors("clearing playlist")
def clear_playlist(playlist_id: str, session: BrowserSession):
    """
    Remove all tracks from a TIDAL playlist.

    Optional JSON payload:
    {
        "chunk_size": 50  // optional, default 50
    }
    """
    data = request.get_json() or {}
    chunk_size = data.get("chunk_size", 50)

    if not isinstance(chunk_size, int) or chunk_size < 1:
        return jsonify({"error": "'chunk_size' must be a positive integer"}), 400

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "clear")
    if error:
        return error

    playlist.clear(chunk_size=chunk_size)

    return jsonify({"status": "success", "message": "Playlist cleared successfully", "playlist_id": playlist_id})


@playlists_bp.route("/api/playlists/<playlist_id>/tracks/reorder", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("reordering playlist tracks")
def reorder_playlist_tracks(playlist_id: str, session: BrowserSession):
    """
    Reorder tracks in a TIDAL playlist by moving tracks to a new position.

    Expected JSON payload:
    {
        "indices": [2, 5, 7],  // list of track indices (0-based), required
        "position": 10         // new position (0-based), required
    }
    """
    data, error = require_json_body(required_fields=["indices", "position"])
    if error:
        return error

    indices = data["indices"]
    position = data["position"]

    if not isinstance(indices, list) or len(indices) == 0:
        return jsonify({"error": "'indices' must be a non-empty list of integers"}), 400

    if not all(isinstance(i, int) for i in indices):
        return jsonify({"error": "All values in 'indices' must be integers"}), 400

    if not isinstance(position, int):
        return jsonify({"error": "'position' must be an integer"}), 400

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "move")
    if error:
        return error

    playlist.move_by_indices(indices, position)

    return jsonify(
        {
            "status": "success",
            "message": f"Moved {len(indices)} track(s) to position {position}",
            "playlist_id": playlist_id,
        }
    )


@playlists_bp.route("/api/playlists/<playlist_id>/merge", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("merging playlists")
def merge_playlists(playlist_id: str, session: BrowserSession):
    """
    Merge tracks from another playlist into this playlist.

    Expected JSON payload:
    {
        "source_playlist_id": "xyz-789",  // required
        "allow_duplicates": false,        // optional, default false
        "allow_missing": true             // optional, default true
    }
    """
    data, error = require_json_body(required_fields=["source_playlist_id"])
    if error:
        return error

    source_playlist_id = data["source_playlist_id"]
    allow_duplicates = data.get("allow_duplicates", False)
    allow_missing = data.get("allow_missing", True)

    # Get target playlist
    target_playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(target_playlist, "merge")
    if error:
        return error

    # Get source playlist
    source_playlist, error = get_playlist_or_404(session, source_playlist_id)
    if error:
        return None, (
            jsonify({"error": f"Source playlist with ID {source_playlist_id} not found"}),
            404,
        )

    # Merge playlists
    added_indices = target_playlist.merge(
        source_playlist, allow_duplicates=allow_duplicates, allow_missing=allow_missing
    )

    return jsonify(
        {
            "status": "success",
            "message": f"Merged {len(added_indices)} tracks from source playlist",
            "playlist_id": playlist_id,
            "source_playlist_id": source_playlist_id,
            "tracks_added": len(added_indices),
        }
    )
