"""Playlist MCP tools."""

import requests
from server import mcp
from utils import (
    FLASK_APP_URL,
    check_tidal_auth,
    error_response,
    handle_api_response,
    validate_list,
    validate_string,
)


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

        response = requests.post(f"{FLASK_APP_URL}/api/playlists", json=payload)

        api_error = handle_api_response(response, "playlist")
        if api_error:
            return api_error

        result = response.json()
        playlist_data = result.get("playlist", {})

        playlist_id = playlist_data.get("id")
        playlist_url = f"https://tidal.com/playlist/{playlist_id}" if playlist_id else None
        playlist_data["playlist_url"] = playlist_url

        return {
            "status": "success",
            "message": f"Successfully created playlist '{title}' with {len(track_ids)} tracks",
            "playlist": playlist_data,
        }

    except Exception as e:
        return error_response(f"Failed to create playlist: {str(e)}")


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
        response = requests.get(f"{FLASK_APP_URL}/api/playlists")

        if response.status_code == 200:
            playlists = response.json().get("playlists", [])
            return {"status": "success", "playlists": playlists, "playlist_count": len(playlists)}

        api_error = handle_api_response(response, "playlists")
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL playlists service: {str(e)}")


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
        response = requests.get(f"{FLASK_APP_URL}/api/playlists/{playlist_id}/tracks", params={"limit": limit})

        if response.status_code == 200:
            data = response.json()
            return {"status": "success", "tracks": data.get("tracks", []), "track_count": data.get("total_tracks", 0)}

        api_error = handle_api_response(response, "playlist", playlist_id)
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL playlist service: {str(e)}")


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
        response = requests.delete(f"{FLASK_APP_URL}/api/playlists/{playlist_id}")

        if response.status_code == 200:
            return response.json()

        api_error = handle_api_response(response, "playlist", playlist_id)
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL playlist service: {str(e)}")


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

        response = requests.post(f"{FLASK_APP_URL}/api/playlists/{playlist_id}/tracks", json=payload)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "message": data.get("message", f"Added {len(track_ids)} tracks to playlist"),
                "playlist_id": playlist_id,
                "added_count": data.get("added_count", len(track_ids)),
                "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
            }

        api_error = handle_api_response(response, "playlist", playlist_id)
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL playlist service: {str(e)}")


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

        response = requests.delete(f"{FLASK_APP_URL}/api/playlists/{playlist_id}/tracks", json=payload)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "message": data.get("message", "Removed tracks from playlist"),
                "playlist_id": playlist_id,
                "removed_count": data.get("removed_count", 0),
                "playlist_url": f"https://tidal.com/playlist/{playlist_id}",
            }

        api_error = handle_api_response(response, "playlist", playlist_id)
        if api_error:
            return api_error

        return response.json()
    except Exception as e:
        return error_response(f"Failed to connect to TIDAL playlist service: {str(e)}")
