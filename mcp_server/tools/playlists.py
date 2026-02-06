"""Playlist MCP tools."""

import logging

import requests
from server import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_delete,
    mcp_get,
    mcp_patch,
    mcp_post,
    validate_list,
    validate_string,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def create_tidal_playlist(title: str, track_ids: list, description: str = "") -> dict:
    """
    Creates a new TIDAL playlist with the specified tracks.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Create a playlist with these songs"
    - "Make a TIDAL playlist"
    - "Save these tracks to a playlist"
    - "Create a collection of songs"
    - Any request to create a new playlist in their TIDAL account

    This function creates a new playlist in the user's TIDAL account and adds the
    specified tracks to it. The user must be authenticated with TIDAL first.

    NAMING CONVENTION GUIDANCE:
    When suggesting or creating a playlist, first check the user's existing playlists
    using get_user_playlists() to understand their naming preferences. Some patterns:
    - Do they use emoji in playlist names?
    - Do they use all caps, title case, or lowercase?
    - Do they include dates or seasons in names?
    - Do they name by mood, genre, activity, or artist?
    - Do they use specific prefixes or formatting

    Try to match their style when suggesting new playlist names.

    When processing the results of this tool:
    1. Confirm the playlist was created successfully
    2. Provide the playlist title, number of tracks added, and URL
    3. Always include the direct TIDAL URL (https://tidal.com/playlist/{playlist_id})
    4. Suggest that the user can now access this playlist in their TIDAL account

    Args:
        title: The name of the playlist to create
        track_ids: List of TIDAL track IDs to add to the playlist
        description: Optional description for the playlist (default: "")

    Returns:
        A dictionary containing the status of the playlist creation and details
    """
    try:
        auth_error = check_tidal_auth("create a playlist")
        if auth_error:
            return auth_error

        title_error = validate_string(title, "playlist title")
        if title_error:
            return title_error

        track_error = validate_list(track_ids, "track_ids", "track ID")
        if track_error:
            return track_error

        payload = {"title": title, "description": description, "track_ids": track_ids}

        result = mcp_post("/api/playlists", "playlist", payload=payload)

        if result.get("status") == "error":
            return result

        playlist_data = result.get("playlist", {})

        playlist_id = playlist_data.get("id")
        playlist_url = f"https://tidal.com/playlist/{playlist_id}" if playlist_id else None
        playlist_data["playlist_url"] = playlist_url

        return {
            "status": "success",
            "message": f"Successfully created playlist '{title}' with {len(track_ids)} tracks",
            "playlist": playlist_data,
        }

    except requests.RequestException as e:
        logger.error("Failed to create playlist", exc_info=True)
        return error_response(f"Failed to create playlist: {e}")


@mcp.tool()
def get_user_playlists() -> dict:
    """
    Fetches the user's playlists from their TIDAL account.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Show me my playlists"
    - "List my TIDAL playlists"
    - "What playlists do I have?"
    - "Get my music collections"
    - Any request to view or list their TIDAL playlists

    This function retrieves the user's playlists from TIDAL and returns them sorted
    by last updated date (most recent first).

    When processing the results of this tool:
    1. Present the playlists in a clear, organized format
    2. Include key information like title, track count, and the TIDAL URL
    3. Mention when each playlist was last updated if available
    4. If the user has many playlists, focus on the most recently updated ones

    Returns:
        A dictionary containing the user's playlists sorted by last updated date
    """
    auth_error = check_tidal_auth("fetch your playlists")
    if auth_error:
        return auth_error

    try:
        data = mcp_get("/api/playlists", "playlists")

        if data.get("status") == "error":
            return data

        playlists = data.get("playlists", [])
        return {"status": "success", "playlists": playlists, "playlist_count": len(playlists)}

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlists service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlists service: {e}")


@mcp.tool()
def get_playlist_tracks(playlist_id: str, limit: int = 50) -> dict:
    """
    Retrieves all tracks from a specified TIDAL playlist.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Show me the songs in my playlist"
    - "What tracks are in my [playlist name] playlist?"
    - "List the songs from my playlist"
    - "Get tracks from my playlist"
    - "View contents of my TIDAL playlist"
    - Any request to see what songs/tracks are in a specific playlist

    This function retrieves all tracks from a specific playlist in the user's
    TIDAL account. The playlist_id must be provided, which can be obtained from
    the get_user_playlists() function.

    When processing the results of this tool:
    1. Present the playlist information (title, description, track count) as context
    2. List the tracks in a clear, organized format with track name, artist, and album
    3. Include track durations where available
    4. Mention the total number of tracks in the playlist
    5. If there are many tracks, focus on highlighting interesting patterns or variety

    Args:
        playlist_id: The TIDAL ID of the playlist to retrieve (required)
        limit: Maximum number of tracks to retrieve (default: 50, max: 5000)

    Returns:
        A dictionary containing the playlist information and all tracks in the playlist
    """
    auth_error = check_tidal_auth("fetch playlist tracks")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    try:
        data = mcp_get(
            f"/api/playlists/{playlist_id}/tracks", "playlist", params={"limit": limit}, resource_id=playlist_id
        )

        if data.get("status") == "error":
            return data

        return {"status": "success", "tracks": data.get("tracks", []), "track_count": data.get("total_tracks", 0)}

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def delete_tidal_playlist(playlist_id: str) -> dict:
    """
    Deletes a TIDAL playlist by its ID.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Delete my playlist"
    - "Remove a playlist from my TIDAL account"
    - "Get rid of this playlist"
    - "Delete the playlist with ID X"
    - Any request to delete or remove a TIDAL playlist

    This function deletes a specific playlist from the user's TIDAL account.
    The user must be authenticated with TIDAL first.

    When processing the results of this tool:
    1. Confirm the playlist was deleted successfully
    2. Provide a clear message about the deletion

    Args:
        playlist_id: The TIDAL ID of the playlist to delete (required)

    Returns:
        A dictionary containing the status of the playlist deletion
    """
    auth_error = check_tidal_auth("delete a playlist")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    try:
        return mcp_delete(f"/api/playlists/{playlist_id}", "playlist", resource_id=playlist_id)

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def add_tracks_to_playlist(
    playlist_id: str, track_ids: list[str], allow_duplicates: bool = False, position: int = -1
) -> dict:
    """
    Add tracks to an existing TIDAL playlist.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Add these songs to my playlist"
    - "Add tracks to [playlist name]"
    - "Put these tracks in my playlist"
    - "Add [song] to my [playlist]"
    - Any request to add songs/tracks to an existing playlist

    This function adds the specified tracks to an existing playlist in the user's
    TIDAL account. The user must be authenticated with TIDAL first.
    Use get_user_playlists() to find playlist IDs, and search_tidal() to find track IDs.

    When processing the results of this tool:
    1. Confirm the tracks were added successfully
    2. Report how many tracks were added
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist to add tracks to (required)
        track_ids: List of TIDAL track IDs to add to the playlist (required)
        allow_duplicates: Whether to allow adding tracks that already exist (default: False)
        position: Position in playlist to insert tracks (-1 = append to end, default: -1)

    Returns:
        A dictionary containing the status of the operation and number of tracks added
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    track_error = validate_list(track_ids, "track_ids", "track ID")
    if track_error:
        return error_response(
            "At least one track ID is required. You can find track IDs using the search_tidal() function."
        )

    try:
        payload = {"track_ids": track_ids, "allow_duplicates": allow_duplicates, "position": position}

        data = mcp_post(f"/api/playlists/{playlist_id}/tracks", "playlist", payload=payload, resource_id=playlist_id)

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", f"Added {len(track_ids)} tracks to playlist"),
            "playlist_id": playlist_id,
            "added_count": data.get("added_count", len(track_ids)),
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def remove_tracks_from_playlist(playlist_id: str, track_ids: list[str]) -> dict:
    """
    Remove tracks from a TIDAL playlist.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Remove these songs from my playlist"
    - "Delete tracks from [playlist name]"
    - "Take [song] out of my playlist"
    - "Remove [song] from my [playlist]"
    - Any request to remove songs/tracks from an existing playlist

    This function removes the specified tracks from an existing playlist in the
    user's TIDAL account. The user must be authenticated with TIDAL first.
    Use get_user_playlists() to find playlist IDs, and get_playlist_tracks() to
    find track IDs in a playlist.

    When processing the results of this tool:
    1. Confirm the tracks were removed successfully
    2. Report how many tracks were removed
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist to remove tracks from (required)
        track_ids: List of TIDAL track IDs to remove from the playlist (required)

    Returns:
        A dictionary containing the status of the operation and number of tracks removed
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    track_error = validate_list(track_ids, "track_ids", "track ID")
    if track_error:
        return error_response(
            "At least one track ID is required."
            " You can find track IDs in a playlist using the get_playlist_tracks() function."
        )

    try:
        payload = {"track_ids": track_ids}

        data = mcp_delete(f"/api/playlists/{playlist_id}/tracks", "playlist", payload=payload, resource_id=playlist_id)

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", "Removed tracks from playlist"),
            "playlist_id": playlist_id,
            "removed_count": data.get("removed_count", 0),
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def edit_tidal_playlist(playlist_id: str, title: str = None, description: str = None) -> dict:
    """
    Edit a TIDAL playlist's metadata (title and/or description).

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Rename my playlist"
    - "Change the description of my playlist"
    - "Update playlist title to [new title]"
    - "Edit my [playlist] playlist"
    - Any request to change playlist metadata

    This function edits an existing playlist's title and/or description.
    At least one of title or description must be provided.
    The user must be authenticated with TIDAL first.

    When processing the results of this tool:
    1. Confirm the playlist was updated successfully
    2. Show the updated title and/or description
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist to edit (required)
        title: New title for the playlist (optional)
        description: New description for the playlist (optional)

    Returns:
        A dictionary containing the status and updated playlist information
    """
    auth_error = check_tidal_auth("edit playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    if title is None and description is None:
        return error_response("At least one of 'title' or 'description' must be provided.")

    if title is not None:
        title_error = validate_string(title, "playlist title")
        if title_error:
            return title_error

    try:
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description

        data = mcp_patch(f"/api/playlists/{playlist_id}", "playlist", payload=payload, resource_id=playlist_id)

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", "Playlist updated successfully"),
            "playlist": data.get("playlist", {}),
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def set_tidal_playlist_visibility(playlist_id: str, public: bool) -> dict:
    """
    Set a TIDAL playlist's visibility (public or private).

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Make my playlist public"
    - "Make my playlist private"
    - "Change playlist visibility"
    - "Set [playlist] to public/private"
    - Any request to change playlist sharing settings

    This function changes a playlist's visibility setting.
    Public playlists can be discovered and shared with others.
    Private playlists are only visible to you.

    When processing the results of this tool:
    1. Confirm the visibility was changed successfully
    2. Mention whether it's now public or private
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist (required)
        public: True to make public, False to make private (required)

    Returns:
        A dictionary containing the status and new visibility setting
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    try:
        visibility = "public" if public else "private"
        data = mcp_post(f"/api/playlists/{playlist_id}/visibility/{visibility}", "playlist", resource_id=playlist_id)

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", f"Playlist is now {visibility}"),
            "playlist_id": playlist_id,
            "public": public,
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def clear_tidal_playlist(playlist_id: str, chunk_size: int = 50) -> dict:
    """
    Remove all tracks from a TIDAL playlist.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Clear my playlist"
    - "Remove all songs from my playlist"
    - "Empty my [playlist] playlist"
    - "Delete all tracks from playlist"
    - Any request to remove all tracks from a playlist

    ⚠️ WARNING: This action is irreversible! All tracks will be permanently removed.

    This function removes all tracks from a playlist in chunks.
    The playlist itself is not deleted, only its contents.

    When processing the results of this tool:
    1. Confirm all tracks were removed
    2. Remind user the playlist still exists (just empty)
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist to clear (required)
        chunk_size: Number of tracks to remove per batch (default: 50)

    Returns:
        A dictionary containing the status of the operation
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    try:
        payload = {"chunk_size": chunk_size}
        data = mcp_delete(
            f"/api/playlists/{playlist_id}/tracks/all", "playlist", payload=payload, resource_id=playlist_id
        )

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", "Playlist cleared successfully"),
            "playlist_id": playlist_id,
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def reorder_tidal_playlist_tracks(playlist_id: str, indices: list[int], position: int) -> dict:
    """
    Reorder tracks in a TIDAL playlist by moving them to a new position.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Move track 3 to position 10"
    - "Reorder tracks in my playlist"
    - "Move the first two songs to the end"
    - "Reorganize my playlist"
    - Any request to change track order in a playlist

    This function moves one or more tracks (specified by their indices) to a new position.
    All indices are 0-based (first track is index 0).

    When processing the results of this tool:
    1. Confirm the tracks were reordered successfully
    2. Mention how many tracks were moved and to which position
    3. Provide a link to the playlist

    Args:
        playlist_id: The TIDAL ID of the playlist (required)
        indices: List of track indices to move, 0-based (required)
        position: Target position to move tracks to, 0-based (required)

    Returns:
        A dictionary containing the status of the operation

    Example:
        # Move tracks at positions 2, 5, and 7 to position 10
        reorder_tidal_playlist_tracks("abc-123", [2, 5, 7], 10)
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    id_error = validate_string(playlist_id, "playlist ID")
    if id_error:
        return error_response(
            "A playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    indices_error = validate_list(indices, "indices", "index")
    if indices_error:
        return error_response("At least one track index is required.")

    if not all(isinstance(i, int) for i in indices):
        return error_response("All indices must be integers.")

    if not isinstance(position, int):
        return error_response("Position must be an integer.")

    try:
        payload = {"indices": indices, "position": position}
        data = mcp_post(
            f"/api/playlists/{playlist_id}/tracks/reorder", "playlist", payload=payload, resource_id=playlist_id
        )

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", f"Moved {len(indices)} track(s) to position {position}"),
            "playlist_id": playlist_id,
            "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")


@mcp.tool()
def merge_tidal_playlists(
    target_playlist_id: str, source_playlist_id: str, allow_duplicates: bool = False, allow_missing: bool = True
) -> dict:
    """
    Merge tracks from one TIDAL playlist into another.

    USE THIS TOOL WHENEVER A USER ASKS FOR:
    - "Combine these two playlists"
    - "Merge [playlist A] into [playlist B]"
    - "Add all tracks from [playlist A] to [playlist B]"
    - "Combine my playlists"
    - Any request to merge or combine playlists

    This function copies all tracks from the source playlist into the target playlist.
    The source playlist is not modified or deleted.

    When processing the results of this tool:
    1. Confirm the merge was successful
    2. Report how many tracks were added
    3. Provide links to both playlists

    Args:
        target_playlist_id: The playlist to merge tracks into (required)
        source_playlist_id: The playlist to copy tracks from (required)
        allow_duplicates: Whether to add tracks that already exist in target (default: False)
        allow_missing: Whether to continue if some tracks are unavailable (default: True)

    Returns:
        A dictionary containing the status and number of tracks added
    """
    auth_error = check_tidal_auth("modify playlists")
    if auth_error:
        return auth_error

    target_error = validate_string(target_playlist_id, "target playlist ID")
    if target_error:
        return error_response(
            "A target playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    source_error = validate_string(source_playlist_id, "source playlist ID")
    if source_error:
        return error_response(
            "A source playlist ID is required. You can get playlist IDs by using the get_user_playlists() function."
        )

    try:
        payload = {
            "source_playlist_id": source_playlist_id,
            "allow_duplicates": allow_duplicates,
            "allow_missing": allow_missing,
        }

        data = mcp_post(
            f"/api/playlists/{target_playlist_id}/merge", "playlist", payload=payload, resource_id=target_playlist_id
        )

        if data.get("status") == "error":
            return data

        return {
            "status": "success",
            "message": data.get("message", "Playlists merged successfully"),
            "target_playlist_id": target_playlist_id,
            "source_playlist_id": source_playlist_id,
            "tracks_added": data.get("tracks_added", 0),
            "target_playlist_url": f"https://tidal.com/playlist/{target_playlist_id}",
            "source_playlist_url": f"https://tidal.com/playlist/{source_playlist_id}",
        }

    except requests.RequestException as e:
        logger.error("Failed to connect to TIDAL playlist service", exc_info=True)
        return error_response(f"Failed to connect to TIDAL playlist service: {e}")
