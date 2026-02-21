"""Artist routes for TIDAL API."""

import logging
import os

from flask import Blueprint, jsonify, request

from tidal_api.utils import (
    bound_limit,
    fetch_all_paginated,
    format_album_data,
    format_artist_data,
    format_artist_detail_data,
    format_track_data,
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
    tidal_album_url,
    tidal_artist_url,
    tidal_track_url,
)

logger = logging.getLogger(__name__)

artists_bp = Blueprint("artists", __name__)

# Standard artist image dimensions (matching tidalapi defaults)
_ARTIST_IMAGE_DIM = 320
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


def _format_artist_dict(artist_data: dict) -> dict:
    """Format a custom-client artist dict into the standard response shape."""
    return {
        "id": artist_data.get("id"),
        "name": artist_data.get("name"),
        "picture_url": _image_url_from_uuid(artist_data.get("picture"), _ARTIST_IMAGE_DIM),
        "url": tidal_artist_url(artist_data.get("id", "")),
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


@artists_bp.route("/api/artists/<artist_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist info")
def get_artist(artist_id: str, session):
    """Get detailed information about an artist."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        artist_data = session.artists.get(artist_id)
        bio = None
        try:
            bio = session.artists.get_bio(artist_id)
        except Exception:
            logger.debug("Bio not available for artist %s", artist_id)

        return jsonify(
            {
                **_format_artist_dict(artist_data),
                "bio": bio,
                "roles": artist_data.get("artistRoles", []),
                "popularity": artist_data.get("popularity"),
            }
        )
    else:  # tidalapi (BrowserSession) path
        artist, error = get_entity_or_404(session, "artist", artist_id)
        if error:
            return error

        bio = None
        try:
            bio = artist.get_bio()
        except Exception:
            logger.debug("Bio not available for artist %s", artist_id)

        return jsonify(format_artist_detail_data(artist, bio=bio))


@artists_bp.route("/api/artists/<artist_id>/top-tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist top tracks")
def get_artist_top_tracks(artist_id: str, session):
    """Get an artist's top tracks."""
    limit = bound_limit(request.args.get("limit", default=20, type=int))

    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        tracks = session.artists.get_top_tracks(artist_id, limit=limit)
        track_list = [_format_track_dict(t) for t in tracks]
    else:  # tidalapi (BrowserSession) path
        artist, error = get_entity_or_404(session, "artist", artist_id)
        if error:
            return error
        tracks = artist.get_top_tracks(limit=limit)
        track_list = [format_track_data(t) for t in tracks]

    return jsonify({"artist_id": artist_id, "tracks": track_list, "total": len(track_list)})


@artists_bp.route("/api/artists/<artist_id>/albums", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist albums")
def get_artist_albums(artist_id: str, session):
    """Get an artist's albums.

    Query params:
        filter: Album type filter — "albums", "ep_singles", "other" (default: "albums")
        limit: Maximum results (default: 50, max: 5000)
    """
    album_filter = request.args.get("filter", "albums")
    limit = bound_limit(request.args.get("limit", default=50, type=int))

    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        albums = session.artists.get_albums(artist_id, filter=album_filter, limit=limit)
        album_list = [_format_album_dict(a) for a in albums]
    else:  # tidalapi (BrowserSession) path
        filter_method_names = {
            "albums": "get_albums",
            "ep_singles": "get_ep_singles",
            "other": "get_other",
        }
        method_name = filter_method_names.get(album_filter)
        if not method_name:
            return jsonify({"error": f"Invalid filter: {album_filter}. Use: albums, ep_singles, other"}), 400

        artist, error = get_entity_or_404(session, "artist", artist_id)
        if error:
            return error

        fetch_fn = getattr(artist, method_name)
        albums = fetch_all_paginated(fetch_fn, limit=limit)
        album_list = [format_album_data(a) for a in albums]

    return jsonify(
        {
            "artist_id": artist_id,
            "filter": album_filter,
            "albums": album_list,
            "total": len(album_list),
        }
    )


@artists_bp.route("/api/artists/<artist_id>/similar", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching similar artists")
def get_similar_artists(artist_id: str, session):
    """Get artists similar to the given artist."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        similar = session.artists.get_similar(artist_id)
        artist_list = [_format_artist_dict(a) for a in similar]
    else:  # tidalapi (BrowserSession) path
        artist, error = get_entity_or_404(session, "artist", artist_id)
        if error:
            return error
        similar = artist.get_similar()
        artist_list = [format_artist_data(a) for a in similar]

    return jsonify({"artist_id": artist_id, "artists": artist_list, "total": len(artist_list)})


@artists_bp.route("/api/artists/<artist_id>/radio", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist radio")
def get_artist_radio(artist_id: str, session):
    """Get radio tracks based on the given artist.

    Note: tidalapi's get_radio() returns up to 100 tracks (hardcoded).
    The limit parameter truncates the result client-side.
    """
    limit = bound_limit(request.args.get("limit", default=100, type=int), max_n=100)

    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        tracks = session.artists.get_radio(artist_id, limit=limit)
        track_list = [_format_track_dict(t) for t in tracks]
    else:  # tidalapi (BrowserSession) path
        artist, error = get_entity_or_404(session, "artist", artist_id)
        if error:
            return error
        tracks = artist.get_radio()
        track_list = [format_track_data(t) for t in tracks[:limit]]

    return jsonify({"artist_id": artist_id, "tracks": track_list, "total": len(track_list)})
