"""Album and track detail routes for TIDAL API."""

import logging
import os

from flask import Blueprint, jsonify, request
from requests import HTTPError

from tidal_api.utils import (
    bound_limit,
    fetch_all_paginated,
    format_album_data,
    format_album_detail_data,
    format_album_from_dict,
    format_lyrics_data,
    format_track_data,
    format_track_detail_data,
    format_track_from_dict,
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
)
from tidal_client.exceptions import TidalAPIError

logger = logging.getLogger(__name__)

albums_bp = Blueprint("albums", __name__)


def _format_album_detail_dict(album_data: dict, review: str | None = None) -> dict:
    """Format a custom-client album dict with additional detail fields."""
    return {
        **format_album_from_dict(album_data),
        "explicit": album_data.get("explicit"),
        "popularity": album_data.get("popularity"),
        "review": review,
    }


@albums_bp.route("/api/albums/<album_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching album info")
def get_album(album_id: str, session):
    """Get detailed information about an album."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        album_data = session.albums.get(album_id)
        review = None
        try:
            review = session.albums.get_review(album_id)
        except TidalAPIError:
            logger.debug("Review not available for album %s", album_id)

        return jsonify(_format_album_detail_dict(album_data, review=review))
    else:  # tidalapi (BrowserSession) path
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
    limit = bound_limit(request.args.get("limit", default=50, type=int))

    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        tracks = session.albums.get_tracks(album_id, limit=limit)
        track_list = [format_track_from_dict(t) for t in tracks]
    else:  # tidalapi (BrowserSession) path
        album, error = get_entity_or_404(session, "album", album_id)
        if error:
            return error

        tracks = fetch_all_paginated(album.tracks, limit=limit)
        track_list = [format_track_data(t) for t in tracks]

    return jsonify({"album_id": album_id, "tracks": track_list, "total": len(track_list)})


@albums_bp.route("/api/albums/<album_id>/similar", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching similar albums")
def get_similar_albums(album_id: str, session):
    """Get albums similar to the given album."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        similar = session.albums.get_similar(album_id)
        album_list = [format_album_from_dict(a) for a in similar]
    else:  # tidalapi (BrowserSession) path
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
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        review = session.albums.get_review(album_id)
        if review is None:
            return jsonify({"error": "No review available for this album"}), 404
        return jsonify({"album_id": album_id, "review": review})
    else:  # tidalapi (BrowserSession) path
        album, error = get_entity_or_404(session, "album", album_id)
        if error:
            return error

        try:
            review = album.review()
        except (HTTPError, Exception):
            return jsonify({"error": "No review available for this album"}), 404

        return jsonify({"album_id": album_id, "review": review})


# Track routes
@albums_bp.route("/api/tracks/<track_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching track info")
def get_track(track_id: str, session):
    """Get detailed information about a track."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        try:
            track_data = session.tracks.get(track_id)
        except TidalAPIError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify(format_track_from_dict(track_data))
    else:  # tidalapi (BrowserSession) path
        track, error = get_entity_or_404(session, "track", track_id)
        if error:
            return error
        return jsonify(format_track_detail_data(track))


@albums_bp.route("/api/tracks/<track_id>/lyrics", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching track lyrics")
def get_track_lyrics(track_id: str, session):
    """Get lyrics for a track."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        lyrics = session.tracks.get_lyrics(track_id)
        if lyrics is None:
            return jsonify({"error": "Lyrics not found"}), 404
        return jsonify({"track_id": track_id, **lyrics})
    else:  # tidalapi (BrowserSession) path
        track, error = get_entity_or_404(session, "track", track_id)
        if error:
            return error

        try:
            lyrics = track.lyrics()
        except Exception:
            return jsonify({"error": "No lyrics available for this track"}), 404

        return jsonify({"track_id": track_id, **format_lyrics_data(lyrics)})
