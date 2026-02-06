"""Album and track detail routes for TIDAL API."""

import logging

from flask import Blueprint, jsonify, request
from requests import HTTPError

from tidal_api.utils import (
    bound_limit,
    fetch_all_paginated,
    format_album_data,
    format_album_detail_data,
    format_lyrics_data,
    format_track_data,
    format_track_detail_data,
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
)

logger = logging.getLogger(__name__)

albums_bp = Blueprint("albums", __name__)


@albums_bp.route("/api/albums/<album_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching album info")
def get_album(album_id: str, session):
    """Get detailed information about an album."""
    album, error = get_entity_or_404(session, "album", album_id)
    if error:
        return error

    review = None
    try:
        review = album.review()
    except (HTTPError, Exception):
        logger.debug("Review not available for album %s", album_id)

    return jsonify(format_album_detail_data(album, review=review))


@albums_bp.route("/api/albums/<album_id>/tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching album tracks")
def get_album_tracks(album_id: str, session):
    """Get tracks from an album."""
    album, error = get_entity_or_404(session, "album", album_id)
    if error:
        return error

    limit = bound_limit(request.args.get("limit", default=50, type=int))

    tracks = fetch_all_paginated(album.tracks, limit=limit)
    track_list = [format_track_data(t) for t in tracks]

    return jsonify({"album_id": album_id, "tracks": track_list, "total": len(track_list)})


@albums_bp.route("/api/albums/<album_id>/similar", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching similar albums")
def get_similar_albums(album_id: str, session):
    """Get albums similar to the given album."""
    album, error = get_entity_or_404(session, "album", album_id)
    if error:
        return error

    try:
        similar = album.similar()
    except Exception:
        logger.debug("Similar albums not available for album %s", album_id)
        similar = []

    album_list = [format_album_data(a) for a in similar]

    return jsonify({"album_id": album_id, "albums": album_list, "total": len(album_list)})


@albums_bp.route("/api/albums/<album_id>/review", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching album review")
def get_album_review(album_id: str, session):
    """Get the review for an album."""
    album, error = get_entity_or_404(session, "album", album_id)
    if error:
        return error

    try:
        review = album.review()
    except (HTTPError, Exception):
        return jsonify({"error": "No review available for this album"}), 404

    return jsonify({"album_id": album_id, "review": review})


@albums_bp.route("/api/tracks/<track_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching track info")
def get_track(track_id: str, session):
    """Get detailed information about a track."""
    track, error = get_entity_or_404(session, "track", track_id)
    if error:
        return error

    return jsonify(format_track_detail_data(track))


@albums_bp.route("/api/tracks/<track_id>/lyrics", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching track lyrics")
def get_track_lyrics(track_id: str, session):
    """Get lyrics for a track."""
    track, error = get_entity_or_404(session, "track", track_id)
    if error:
        return error

    try:
        lyrics = track.lyrics()
    except Exception:
        return jsonify({"error": "No lyrics available for this track"}), 404

    return jsonify({"track_id": track_id, **format_lyrics_data(lyrics)})
