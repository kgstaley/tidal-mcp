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
    format_lyrics_data,
    format_track_data,
    format_track_detail_data,
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
    tidal_album_url,
    tidal_track_url,
)

logger = logging.getLogger(__name__)

albums_bp = Blueprint("albums", __name__)

# Standard image dimensions for album cover art
_ALBUM_IMAGE_DIM = 640


def _image_url_from_uuid(uuid: str | None, dim: int) -> str | None:
    """Build TIDAL CDN image URL from a picture UUID.

    TIDAL returns picture UUIDs (e.g., "abc1-de23-..."). The CDN URL is
    formed by replacing hyphens with slashes and appending {dim}x{dim}.jpg.
    """
    if not uuid:
        return None
    path = uuid.replace("-", "/")
    return f"https://resources.tidal.com/images/{path}/{dim}x{dim}.jpg"


def _format_album_dict(album_data: dict) -> dict:
    """Format a custom-client album dict into the standard response shape."""
    artist = album_data.get("artist") or {}
    album_id = album_data.get("id", "")
    return {
        "id": album_id,
        "name": album_data.get("title"),
        "artist": artist.get("name", "Unknown"),
        "cover_url": _image_url_from_uuid(album_data.get("cover"), _ALBUM_IMAGE_DIM),
        "release_date": str(album_data["releaseDate"]) if album_data.get("releaseDate") else None,
        "num_tracks": album_data.get("numberOfTracks"),
        "duration": album_data.get("duration"),
        "url": tidal_album_url(album_id),
    }


def _format_album_detail_dict(album_data: dict, review: str | None = None) -> dict:
    """Format a custom-client album dict with additional detail fields."""
    return {
        **_format_album_dict(album_data),
        "explicit": album_data.get("explicit"),
        "popularity": album_data.get("popularity"),
        "review": review,
    }


def _format_track_dict(track_data: dict) -> dict:
    """Format a custom-client track dict into the standard response shape."""
    artist = track_data.get("artist") or {}
    album = track_data.get("album") or {}
    track_id = track_data.get("id", "")
    return {
        "id": track_id,
        "title": track_data.get("title"),
        "artist": artist.get("name", "Unknown"),
        "album": album.get("title", "Unknown"),
        "duration": track_data.get("duration"),
        "url": tidal_track_url(track_id),
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
        except Exception:
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
        track_list = [_format_track_dict(t) for t in tracks]
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
        try:
            similar = session.albums.get_similar(album_id)
        except Exception:
            logger.debug("Similar albums not available for album %s", album_id)
            similar = []
        album_list = [_format_album_dict(a) for a in similar]
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


# Track routes — tidalapi path only until session.tracks is implemented (Task 10)
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
