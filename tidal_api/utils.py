import functools
from flask import jsonify, request


def handle_endpoint_errors(operation: str):
    """
    Decorator wrapping Flask endpoints with try-except.

    Args:
        operation: Description of the operation (e.g., "fetching tracks", "creating playlist")

    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Error {operation}: {str(e)}"}), 500
        return wrapper
    return decorator


def safe_attr(obj, attr: str, default=None):
    """
    Safely get an attribute from an object with fallback.

    Args:
        obj: Object to get attribute from
        attr: Attribute name
        default: Default value if attribute doesn't exist

    Returns:
        Attribute value or default
    """
    return getattr(obj, attr, default) if hasattr(obj, attr) else default


def tidal_track_url(track_id) -> str:
    """Build TIDAL track URL."""
    return f"https://tidal.com/browse/track/{track_id}?u"


def tidal_artist_url(artist_id) -> str:
    """Build TIDAL artist URL."""
    return f"https://tidal.com/browse/artist/{artist_id}"


def tidal_album_url(album_id) -> str:
    """Build TIDAL album URL."""
    return f"https://tidal.com/browse/album/{album_id}"


def tidal_playlist_url(playlist_id) -> str:
    """Build TIDAL playlist URL."""
    return f"https://tidal.com/playlist/{playlist_id}"


def tidal_video_url(video_id) -> str:
    """Build TIDAL video URL."""
    return f"https://tidal.com/browse/video/{video_id}"


def format_user_playlist_data(playlist) -> dict:
    """
    Format a user playlist object into a standardized dictionary.

    Args:
        playlist: TIDAL playlist object

    Returns:
        Dictionary with standardized playlist information
    """
    return {
        "id": playlist.id,
        "title": safe_attr(playlist, 'name'),
        "description": safe_attr(playlist, 'description', ""),
        "created": safe_attr(playlist, 'created'),
        "last_updated": safe_attr(playlist, 'last_updated'),
        "track_count": safe_attr(playlist, 'num_tracks', 0),
        "duration": safe_attr(playlist, 'duration', 0),
        "url": tidal_playlist_url(playlist.id)
    }


def format_track_data(track, source_track_id=None):
    """
    Format a track object into a standardized dictionary.

    Args:
        track: TIDAL track object
        source_track_id: Optional ID of the track that led to this recommendation

    Returns:
        Dictionary with standardized track information
    """
    track_data = {
        "id": track.id,
        "title": track.name,
        "artist": safe_attr(track.artist, 'name', "Unknown"),
        "album": safe_attr(track.album, 'name', "Unknown"),
        "duration": safe_attr(track, 'duration', 0),
        "url": tidal_track_url(track.id)
    }

    # Include source track ID if provided
    if source_track_id:
        track_data["source_track_id"] = source_track_id

    return track_data


def bound_limit(limit: int, max_n: int = 5000) -> int:
    """Ensure limit is within reasonable bounds."""
    if limit < 1:
        limit = 1
    elif limit > max_n:
        limit = max_n
    return limit


def fetch_all_paginated(fetch_fn, limit: int, page_size: int = 50) -> list:
    """
    Fetch items with pagination, batching requests until limit is reached.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of items
        limit: Total number of items to fetch
        page_size: Number of items per request (default 50, TIDAL's limit)

    Returns:
        List of all fetched items up to the limit
    """
    all_items = []
    offset = 0

    while len(all_items) < limit:
        batch_limit = min(page_size, limit - len(all_items))
        batch = fetch_fn(limit=batch_limit, offset=offset)

        if not batch:
            break

        all_items.extend(batch)

        if len(batch) < batch_limit:
            break

        offset += len(batch)

    return all_items[:limit]


def format_artist_data(artist):
    """
    Format an artist object into a standardized dictionary.

    Args:
        artist: TIDAL artist object

    Returns:
        Dictionary with standardized artist information
    """
    picture_url = None
    if hasattr(artist, 'picture') and callable(artist.picture):
        picture_url = artist.picture(640)

    return {
        "id": artist.id,
        "name": artist.name,
        "picture_url": picture_url,
        "url": tidal_artist_url(artist.id)
    }


def format_album_data(album):
    """
    Format an album object into a standardized dictionary.

    Args:
        album: TIDAL album object

    Returns:
        Dictionary with standardized album information
    """
    artist_name = "Unknown"
    if hasattr(album, 'artist'):
        artist_name = safe_attr(album.artist, 'name', "Unknown")

    cover_url = None
    if hasattr(album, 'image') and callable(album.image):
        cover_url = album.image(640)

    release_date = safe_attr(album, 'release_date')
    if release_date is not None:
        release_date = str(release_date)

    return {
        "id": album.id,
        "name": album.name,
        "artist": artist_name,
        "cover_url": cover_url,
        "release_date": release_date,
        "num_tracks": safe_attr(album, 'num_tracks'),
        "duration": safe_attr(album, 'duration'),
        "url": tidal_album_url(album.id)
    }


def format_playlist_search_data(playlist):
    """
    Format a playlist object from search results into a standardized dictionary.

    Args:
        playlist: TIDAL playlist object

    Returns:
        Dictionary with standardized playlist information
    """
    creator_name = None
    if hasattr(playlist, 'creator') and playlist.creator:
        creator_name = safe_attr(playlist.creator, 'name')

    return {
        "id": playlist.id,
        "title": safe_attr(playlist, 'name'),
        "creator": creator_name,
        "track_count": safe_attr(playlist, 'num_tracks', 0),
        "duration": safe_attr(playlist, 'duration', 0),
        "url": tidal_playlist_url(playlist.id)
    }


def format_video_data(video):
    """
    Format a video object into a standardized dictionary.

    Args:
        video: TIDAL video object

    Returns:
        Dictionary with standardized video information
    """
    artist_name = "Unknown"
    if hasattr(video, 'artist'):
        artist_name = safe_attr(video.artist, 'name', "Unknown")

    return {
        "id": video.id,
        "title": safe_attr(video, 'name'),
        "artist": artist_name,
        "duration": safe_attr(video, 'duration'),
        "url": tidal_video_url(video.id)
    }


def get_playlist_or_404(session, playlist_id: str):
    """
    Get a playlist from TIDAL or return None with error response.

    Args:
        session: Authenticated TIDAL session
        playlist_id: The playlist ID to fetch

    Returns:
        Tuple of (playlist, None) if found, or (None, error_response) if not found
    """
    playlist = session.playlist(playlist_id)
    if not playlist:
        return None, (jsonify({"error": f"Playlist with ID {playlist_id} not found"}), 404)
    return playlist, None


def require_json_body(required_fields: list = None):
    """
    Get JSON body from request or return error.

    Args:
        required_fields: Optional list of field names that must be present

    Returns:
        Tuple of (data, None) if valid, or (None, error_response) if invalid
    """
    data = request.get_json()
    if not data:
        return None, (jsonify({"error": "Missing request body"}), 400)

    if required_fields:
        for field in required_fields:
            if field not in data:
                return None, (jsonify({"error": f"Missing '{field}' in request body"}), 400)
            if isinstance(data[field], list) and not data[field]:
                return None, (jsonify({"error": f"No {field} provided"}), 400)

    return data, None


def check_user_playlist(playlist, operation: str = "modify"):
    """
    Check if a playlist is a user playlist with modification capabilities.

    Args:
        playlist: The playlist object to check
        operation: "add" or "remove"

    Returns:
        None if OK, or error response tuple if not a user playlist
    """
    if operation == "add" and not hasattr(playlist, 'add'):
        return jsonify({"error": "Cannot modify this playlist - not a user playlist"}), 403
    if operation == "remove" and not hasattr(playlist, 'remove_by_id'):
        return jsonify({"error": "Cannot modify this playlist - not a user playlist"}), 403
    return None
