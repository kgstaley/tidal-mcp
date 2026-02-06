"""Track MCP tools (favorites, recommendations)."""

import logging

import requests
from server import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_get,
    mcp_post,
    validate_list,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_favorite_tracks(limit: int = 50) -> dict:
    """
    Retrieves tracks from the user's TIDAL account favorites.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "What are my favorite tracks?"
    - "Show me my TIDAL favorites"
    - "What music do I have saved?"
    - "Get my favorite songs"
    - Any request to view their saved/favorite tracks

    This function retrieves the user's favorite tracks from TIDAL.

    Args:
        limit: Maximum number of tracks to retrieve (default: 50, max: 5000).

    Returns:
        A dictionary containing track information including track ID, title, artist, album, and duration.
        Returns an error message if not authenticated or if retrieval fails.
    """
    try:
        auth_error = check_tidal_auth("fetch your favorite tracks")
        if auth_error:
            return auth_error

        return mcp_get("/api/tracks", "tracks", params={"limit": limit})

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL tracks service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL tracks service: {e}")


def _get_tidal_recommendations(track_ids: list = None, limit_per_track: int = 20, filter_criteria: str = None) -> dict:
    """
    [INTERNAL USE] Gets raw recommendation data from TIDAL API.

    Args:
        track_ids: List of TIDAL track IDs to use as seeds for recommendations.
        limit_per_track: Maximum number of recommendations to get per track (default: 20)
        filter_criteria: Optional string describing criteria to filter recommendations

    Returns:
        A dictionary containing recommended tracks based on seed tracks and filtering criteria.
    """
    try:
        validation_error = validate_list(track_ids, "track_ids", "track ID")
        if validation_error:
            return error_response("No track IDs provided for recommendations.")

        payload = {"track_ids": track_ids, "limit_per_track": limit_per_track, "remove_duplicates": True}

        data = mcp_post("/api/recommendations/batch", "recommendations", payload=payload)

        if data.get("status") == "error":
            return data

        recommendations = data.get("recommendations", [])

        result = {"recommendations": recommendations, "total_count": len(recommendations)}

        if filter_criteria:
            result["filter_criteria"] = filter_criteria

        return result

    except requests.RequestException as e:
        logger.error("Failed to get recommendations", exc_info=True)
        return error_response(f"Failed to get recommendations: {e}")


@mcp.tool()
def recommend_tracks(
    track_ids: list[str] | None = None,
    filter_criteria: str | None = None,
    limit_per_track: int = 20,
    limit_from_favorite: int = 20,
) -> dict:
    """
    Recommends music tracks based on specified track IDs or can use the user's
    TIDAL favorites if no IDs are provided.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - Music recommendations
    - Track suggestions
    - Music similar to their TIDAL favorites or specific tracks
    - "What should I listen to?"
    - Any request to recommend songs/tracks/music based on their TIDAL history or specific tracks

    This function gets recommendations based on provided track IDs or retrieves the user's
    favorite tracks as seeds if no IDs are specified.

    When processing the results of this tool:
    1. Analyze the seed tracks to understand the music taste or direction
    2. Review the recommended tracks from TIDAL
    3. IMPORTANT: Do NOT include any tracks from the seed tracks in your recommendations
    4. Ensure there are NO DUPLICATES in your recommended tracks list
    5. Select and rank the most appropriate tracks based on the seed tracks and filter criteria
    6. Group recommendations by similar styles, artists, or moods with descriptive headings
    7. For each recommended track, provide:
       - The track name, artist, album
       - Always include the track's URL to make it easy for users to listen to the track
       - A brief explanation of why this track might appeal to the user based on the seed tracks
       - If applicable, how this track matches their specific filter criteria
    8. Format your response as a nicely presented list of recommendations
       with helpful context (remember to include the track's URL!)
    9. Begin with a brief introduction explaining your selection strategy
    10. Lastly, unless specified otherwise, you should recommend MINIMUM
        20 tracks (or more if possible) to give the user a good variety.

    [IMPORTANT NOTE] If you're not familiar with any artists or tracks
    mentioned, you should use internet search capabilities if available
    to provide more accurate information.

    Args:
        track_ids: Optional list of TIDAL track IDs to use as seeds for recommendations.
                  If not provided, will use the user's favorite tracks.
        filter_criteria: Specific preferences for filtering recommendations (e.g., "relaxing music,"
                         "recent releases," "upbeat," "jazz influences")
        limit_per_track: Maximum number of recommendations to get per track
                         (NOTE: default 20, keep large enough for enough candidates)
        limit_from_favorite: Maximum number of favorite tracks to use as seeds
                             (NOTE: default 20, keep large enough for enough candidates)

    Returns:
        A dictionary containing both the seed tracks and recommended tracks
    """
    auth_error = check_tidal_auth("recommend music")
    if auth_error:
        return auth_error

    seed_track_ids = []
    seed_tracks_info = []

    if track_ids and isinstance(track_ids, list) and len(track_ids) > 0:
        seed_track_ids = track_ids
    else:
        tracks_response = get_favorite_tracks(limit=limit_from_favorite)

        if "status" in tracks_response and tracks_response["status"] == "error":
            return {
                "status": "error",
                "message": f"Unable to get favorite tracks for recommendations: {tracks_response['message']}",
            }

        favorite_tracks = tracks_response.get("tracks", [])

        if not favorite_tracks:
            return {
                "status": "error",
                "message": (
                    "I couldn't find any favorite tracks in your TIDAL account to use as seeds for recommendations."
                ),
            }

        seed_track_ids = [track["id"] for track in favorite_tracks]
        seed_tracks_info = favorite_tracks

    recommendations_response = _get_tidal_recommendations(
        track_ids=seed_track_ids, limit_per_track=limit_per_track, filter_criteria=filter_criteria
    )

    if "status" in recommendations_response and recommendations_response["status"] == "error":
        return {"status": "error", "message": f"Unable to get recommendations: {recommendations_response['message']}"}

    recommendations = recommendations_response.get("recommendations", [])

    if not recommendations:
        return {
            "status": "error",
            "message": (
                "I couldn't find any recommendations based on the provided tracks."
                " Please try again with different tracks or adjust your filtering criteria."
            ),
        }

    return {
        "status": "success",
        "seed_tracks": seed_tracks_info,
        "seed_track_ids": seed_track_ids,
        "recommendations": recommendations,
        "filter_criteria": filter_criteria,
        "seed_count": len(seed_track_ids),
    }
