"""Mix routes for TIDAL API."""

import logging
import os

from flask import Blueprint, jsonify, request

from tidal_api.utils import (
    bound_limit,
    format_mix_data,
    format_mix_from_dict,
    format_track_data,
    format_track_from_dict,
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
)

logger = logging.getLogger(__name__)

mixes_bp = Blueprint("mixes", __name__)


@mixes_bp.route("/api/mixes", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching user mixes")
def get_user_mixes(session):
    """Get user's mixes."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        mixes_data = session.mixes.get_user_mixes()
        formatted_mixes = [format_mix_from_dict(m) for m in mixes_data]
        return jsonify({"mixes": formatted_mixes, "count": len(formatted_mixes)})
    else:
        page = session.mixes()

        all_mixes = []
        if hasattr(page, "categories") and page.categories:
            for category in page.categories:
                if hasattr(category, "items") and category.items:
                    all_mixes.extend(category.items)

        formatted_mixes = [format_mix_data(mix) for mix in all_mixes]
        return jsonify({"mixes": formatted_mixes, "count": len(formatted_mixes)})


@mixes_bp.route("/api/mixes/<mix_id>/tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching mix tracks")
def get_mix_tracks(mix_id: str, session):
    """Get tracks in a mix."""
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"
    if use_custom:
        limit = bound_limit(request.args.get("limit", 50, type=int))
        tracks_data = session.mixes.get_mix_tracks(mix_id)
        tracks_data = tracks_data[:limit]
        formatted_tracks = [format_track_from_dict(t) for t in tracks_data]
        return jsonify({"tracks": formatted_tracks, "count": len(formatted_tracks)})
    else:
        mix, error = get_entity_or_404(session, "mix", mix_id)
        if error:
            return error

        limit = request.args.get("limit", 50, type=int)
        limit = bound_limit(limit)

        items = mix.items()

        # Filter to only tracks (exclude videos)
        tracks = [item for item in items if hasattr(item, "artist") and hasattr(item, "album")]
        tracks = tracks[:limit]

        formatted_tracks = [format_track_data(track) for track in tracks]
        return jsonify({"tracks": formatted_tracks, "count": len(formatted_tracks)})
