"""Playlist routes for TIDAL API."""

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
    for track_id in track_ids:
        try:
            playlist.remove_by_id(track_id)
            removed_count += 1
        except Exception:
            pass

    return jsonify(
        {
            "status": "success",
            "message": f"Removed {removed_count} tracks from playlist",
            "playlist_id": playlist_id,
            "removed_count": removed_count,
        }
    )
