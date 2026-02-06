"""Track routes for TIDAL API (favorites, recommendations)."""

import concurrent.futures
import logging

from flask import Blueprint, jsonify, request

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import (
    bound_limit,
    fetch_all_paginated,
    format_track_data,
    handle_endpoint_errors,
    require_json_body,
    requires_tidal_auth,
)

logger = logging.getLogger(__name__)

tracks_bp = Blueprint("tracks", __name__)


@tracks_bp.route("/api/tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching tracks")
def get_tracks(session: BrowserSession):
    """
    Get tracks from the user's favorites.
    """
    favorites = session.user.favorites

    limit = bound_limit(request.args.get("limit", default=50, type=int))

    tracks = fetch_all_paginated(
        lambda lim, off: favorites.tracks(limit=lim, offset=off, order="DATE", order_direction="DESC"), limit=limit
    )
    track_list = [format_track_data(track) for track in tracks]

    return jsonify({"tracks": track_list, "total": len(track_list)})


@tracks_bp.route("/api/recommendations/track/<track_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching recommendations")
def get_track_recommendations(track_id: str, session: BrowserSession):
    """
    Get recommended tracks based on a specific track using TIDAL's track radio feature.
    """
    limit = bound_limit(request.args.get("limit", default=10, type=int))

    track = session.track(track_id)
    if not track:
        return jsonify({"error": f"Track with ID {track_id} not found"}), 404

    recommendations = track.get_track_radio(limit=limit)

    track_list = [format_track_data(t) for t in recommendations]
    return jsonify({"recommendations": track_list})


@tracks_bp.route("/api/recommendations/batch", methods=["POST"])
@requires_tidal_auth
@handle_endpoint_errors("fetching batch recommendations")
def get_batch_recommendations(session: BrowserSession):
    """
    Get recommended tracks based on a list of track IDs using concurrent requests.
    """
    data, error = require_json_body(required_fields=["track_ids"])
    if error:
        return error

    track_ids = data["track_ids"]
    if not isinstance(track_ids, list):
        return jsonify({"error": "track_ids must be a list"}), 400

    limit_per_track = bound_limit(data.get("limit_per_track", 20))
    remove_duplicates = data.get("remove_duplicates", True)

    def get_single_track_recommendations(tid):
        """Function to get recommendations for a single track"""
        try:
            track = session.track(tid)
            recommendations = track.get_track_radio(limit=limit_per_track)
            return [format_track_data(rec, source_track_id=tid) for rec in recommendations]
        except Exception as e:
            logger.warning("Error getting recommendations for track %s: %s", tid, e)
            return []

    all_recommendations = []
    seen_track_ids = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(track_ids), 10)) as executor:
        future_to_track_id = {executor.submit(get_single_track_recommendations, tid): tid for tid in track_ids}

        for future in concurrent.futures.as_completed(future_to_track_id):
            track_recommendations = future.result()

            for track_data in track_recommendations:
                tid = track_data.get("id")

                if remove_duplicates and tid in seen_track_ids:
                    continue

                all_recommendations.append(track_data)
                seen_track_ids.add(tid)

    return jsonify({"recommendations": all_recommendations})
