"""Search routes for TIDAL API."""

import os

import tidalapi
from flask import Blueprint, jsonify, request

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import (
    bound_limit,
    format_album_data,
    format_album_from_dict,
    format_artist_data,
    format_artist_from_dict,
    format_playlist_from_dict,
    format_playlist_search_data,
    format_track_data,
    format_track_from_dict,
    format_video_data,
    format_video_from_dict,
    handle_endpoint_errors,
    requires_tidal_auth,
)

search_bp = Blueprint("search", __name__)

VALID_SEARCH_TYPES = {"artists", "tracks", "albums", "playlists", "videos"}


@search_bp.route("/api/search", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("searching")
def search(session: BrowserSession):
    """
    Search TIDAL catalog for artists, tracks, albums, playlists, and videos.

    Query params:
        query: Search query string (required)
        types: Comma-separated list of content types (artists,tracks,albums,playlists,videos)
        limit: Maximum results per type (default: 20, max: 50)
    """
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    types_param = request.args.get("types", "")
    limit = bound_limit(request.args.get("limit", default=20, type=int))

    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"

    if use_custom:
        types_list = None
        if types_param:
            parsed = [t.strip().lower() for t in types_param.split(",")]
            parsed = [t for t in parsed if t in VALID_SEARCH_TYPES]
            if parsed:
                types_list = parsed

        results = session.search.search(query, types=types_list, limit=limit)

        # top_hit is not supported by the custom client API; only returned in tidalapi mode
        return jsonify(
            {
                "query": query,
                "artists": [format_artist_from_dict(a) for a in results.get("artists", [])],
                "tracks": [format_track_from_dict(t) for t in results.get("tracks", [])],
                "albums": [format_album_from_dict(a) for a in results.get("albums", [])],
                "playlists": [format_playlist_from_dict(p) for p in results.get("playlists", [])],
                "videos": [format_video_from_dict(v) for v in results.get("videos", [])],
            }
        )
    else:  # tidalapi (BrowserSession) path — unchanged
        type_map = {
            "artists": tidalapi.Artist,
            "tracks": tidalapi.Track,
            "albums": tidalapi.Album,
            "playlists": tidalapi.Playlist,
            "videos": tidalapi.Video,
        }

        models = None
        if types_param:
            types_list = [t.strip().lower() for t in types_param.split(",")]
            models = [type_map[t] for t in types_list if t in type_map]
            if not models:
                models = None

        results = session.search(query, models=models, limit=limit)

        response = {
            "query": query,
            "artists": [format_artist_data(a) for a in results.get("artists", [])],
            "tracks": [format_track_data(t) for t in results.get("tracks", [])],
            "albums": [format_album_data(a) for a in results.get("albums", [])],
            "playlists": [format_playlist_search_data(p) for p in results.get("playlists", [])],
            "videos": [format_video_data(v) for v in results.get("videos", [])],
        }

        top_hit = results.get("top_hit")
        if top_hit:
            top_hit_type = type(top_hit).__name__.lower()
            if top_hit_type == "artist":
                response["top_hit"] = {"type": "artist", "data": format_artist_data(top_hit)}
            elif top_hit_type == "track":
                response["top_hit"] = {"type": "track", "data": format_track_data(top_hit)}
            elif top_hit_type == "album":
                response["top_hit"] = {"type": "album", "data": format_album_data(top_hit)}
            elif top_hit_type == "playlist":
                response["top_hit"] = {"type": "playlist", "data": format_playlist_search_data(top_hit)}
            elif top_hit_type == "video":
                response["top_hit"] = {"type": "video", "data": format_video_data(top_hit)}

        return jsonify(response)
