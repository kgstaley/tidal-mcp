import functools
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from flask import jsonify, request

logger = logging.getLogger(__name__)

# --- Constants ---
MAX_LIMIT = 5000
DEFAULT_PAGE_SIZE = 50

# Standard image dimensions for TIDAL CDN thumbnails
ARTIST_IMAGE_DIM = 320
ALBUM_IMAGE_DIM = 640

# Session file path
token_path = os.path.join(tempfile.gettempdir(), "tidal-session-oauth.json")
SESSION_FILE = Path(token_path)


def _create_tidal_session():
    """
    Create TIDAL session - BrowserSession or custom client based on env var.

    Returns:
        Either BrowserSession (tidalapi) or TidalSession (custom client)

    Raises:
        ValueError: If custom client is enabled without credentials
    """
    use_custom = os.getenv("TIDAL_USE_CUSTOM_CLIENT", "false").lower() == "true"

    if use_custom:
        # Use custom client
        from tidal_client.config import Config
        from tidal_client.session import TidalSession

        client_id = os.getenv("TIDAL_CLIENT_ID")
        client_secret = os.getenv("TIDAL_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET required for custom client")

        config = Config(client_id=client_id, client_secret=client_secret)
        session = TidalSession(config)

        # Load saved session if exists
        if SESSION_FILE.exists():
            session.load_session(SESSION_FILE)

        return session
    else:
        # Use existing BrowserSession (tidalapi wrapper)
        from tidal_api.browser_session import BrowserSession

        return BrowserSession()


def requires_tidal_auth(f):
    """
    Decorator to ensure routes have an authenticated TIDAL session.
    Returns 401 if not authenticated.
    Passes the authenticated session to the decorated function.

    Supports both BrowserSession (tidalapi) and TidalSession (custom client):
    - BrowserSession: calls login_session_file_auto() to load + validate
    - TidalSession: session already loaded in _create_tidal_session(), checks _is_token_valid()
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not SESSION_FILE.exists():
            return jsonify({"error": "Not authenticated"}), 401

        session = _create_tidal_session()

        # Duck-type: BrowserSession has login_session_file_auto; TidalSession does not
        if hasattr(session, "login_session_file_auto"):
            login_success = session.login_session_file_auto(SESSION_FILE)
            if not login_success:
                return jsonify({"error": "Authentication failed"}), 401
        elif not session._is_token_valid():
            return jsonify({"error": "Authentication failed"}), 401

        kwargs["session"] = session
        return f(*args, **kwargs)

    return decorated_function


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
    return getattr(obj, attr, default)


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


def tidal_image_url(uuid: str | None, dim: int) -> str | None:
    """Build TIDAL CDN image URL from a picture UUID.

    TIDAL returns picture UUIDs (e.g., "abc1-de23-..."). The CDN URL is
    formed by replacing hyphens with slashes and appending {dim}x{dim}.jpg.

    Args:
        uuid: TIDAL picture UUID string, or None
        dim: Image dimension (e.g. 320 for artists, 640 for albums)

    Returns:
        Full CDN URL string, or None if uuid is falsy
    """
    if not uuid:
        return None
    path = uuid.replace("-", "/")
    return f"https://resources.tidal.com/images/{path}/{dim}x{dim}.jpg"


def format_track_from_dict(track_data: dict) -> dict:
    """Format a custom-client track dict into the standard response shape.

    Args:
        track_data: Raw track dict from custom client API

    Returns:
        Standardized track dict matching format_track_data() output shape
    """
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


def format_album_from_dict(album_data: dict) -> dict:
    """Format a custom-client album dict into the standard response shape.

    Args:
        album_data: Raw album dict from custom client API

    Returns:
        Standardized album dict matching format_album_data() output shape
    """
    artist = album_data.get("artist") or {}
    album_id = album_data.get("id", "")
    return {
        "id": album_id,
        "name": album_data.get("title"),
        "artist": artist.get("name", "Unknown"),
        "cover_url": tidal_image_url(album_data.get("cover"), ALBUM_IMAGE_DIM),
        "release_date": str(album_data["releaseDate"]) if album_data.get("releaseDate") else None,
        "num_tracks": album_data.get("numberOfTracks"),
        "duration": album_data.get("duration"),
        "url": tidal_album_url(album_id),
    }


def format_artist_from_dict(artist_data: dict) -> dict:
    """Format a custom-client artist dict into the standard response shape.

    Args:
        artist_data: Raw artist dict from custom client API

    Returns:
        Standardized artist dict matching format_artist_data() output shape
    """
    artist_id = artist_data.get("id", "")
    return {
        "id": artist_id,
        "name": artist_data.get("name"),
        "picture_url": tidal_image_url(artist_data.get("picture"), ARTIST_IMAGE_DIM),
        "url": tidal_artist_url(artist_id),
    }


def format_playlist_from_dict(playlist_data: dict) -> dict:
    """Format a custom-client playlist dict into the standard response shape.

    Args:
        playlist_data: Raw playlist dict from custom client API

    Returns:
        Standardized playlist dict matching format_playlist_search_data() output shape
    """
    playlist_id = playlist_data.get("uuid", "")
    creator = playlist_data.get("creator") or {}
    return {
        "id": playlist_id,
        "title": playlist_data.get("title"),
        "creator": creator.get("name"),
        "track_count": playlist_data.get("numberOfTracks", 0),
        "duration": playlist_data.get("duration", 0),
        "url": tidal_playlist_url(playlist_id),
    }


def format_video_from_dict(video_data: dict) -> dict:
    """Format a custom-client video dict into the standard response shape.

    Args:
        video_data: Raw video dict from custom client API

    Returns:
        Standardized video dict matching format_video_data() output shape
    """
    video_id = video_data.get("id", "")
    artist = video_data.get("artist") or {}
    return {
        "id": video_id,
        "title": video_data.get("title"),
        "artist": artist.get("name", "Unknown"),
        "duration": video_data.get("duration"),
        "url": tidal_video_url(video_id),
    }


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
        "title": safe_attr(playlist, "name"),
        "description": safe_attr(playlist, "description", ""),
        "created": safe_attr(playlist, "created"),
        "last_updated": safe_attr(playlist, "last_updated"),
        "track_count": safe_attr(playlist, "num_tracks", 0),
        "duration": safe_attr(playlist, "duration", 0),
        "url": tidal_playlist_url(playlist.id),
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
        "artist": safe_attr(track.artist, "name", "Unknown"),
        "album": safe_attr(track.album, "name", "Unknown"),
        "duration": safe_attr(track, "duration", 0),
        "url": tidal_track_url(track.id),
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


def format_artist_data(artist) -> dict:
    """
    Format an artist object into a standardized dictionary.

    Args:
        artist: TIDAL artist object

    Returns:
        Dictionary with standardized artist information
    """
    picture_url = None
    if hasattr(artist, "image") and callable(artist.image):
        try:
            picture_url = artist.image(320)
        except ValueError:
            pass

    return {"id": artist.id, "name": artist.name, "picture_url": picture_url, "url": tidal_artist_url(artist.id)}


def format_artist_detail_data(artist, bio: str = None) -> dict:
    """
    Format an artist object with extended details (bio, roles).

    Extends format_artist_data with additional metadata.

    Args:
        artist: TIDAL artist object
        bio: Optional pre-fetched biography text

    Returns:
        Dictionary with detailed artist information
    """
    raw_roles = safe_attr(artist, "roles") or []
    roles = [r.value if hasattr(r, "value") else str(r) for r in raw_roles]

    return {
        **format_artist_data(artist),
        "bio": bio,
        "roles": roles,
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
    if hasattr(album, "artist"):
        artist_name = safe_attr(album.artist, "name", "Unknown")

    cover_url = None
    if hasattr(album, "image") and callable(album.image):
        cover_url = album.image(640)

    release_date = safe_attr(album, "release_date")
    if release_date is not None:
        release_date = str(release_date)

    return {
        "id": album.id,
        "name": album.name,
        "artist": artist_name,
        "cover_url": cover_url,
        "release_date": release_date,
        "num_tracks": safe_attr(album, "num_tracks"),
        "duration": safe_attr(album, "duration"),
        "url": tidal_album_url(album.id),
    }


def format_album_detail_data(album, review: str = None) -> dict:
    """
    Format an album object with extended details.

    Extends format_album_data with additional metadata.

    Args:
        album: TIDAL album object
        review: Optional pre-fetched review text

    Returns:
        Dictionary with detailed album information
    """
    tidal_release_date = safe_attr(album, "tidal_release_date")
    if tidal_release_date is not None:
        tidal_release_date = str(tidal_release_date)

    audio_modes = safe_attr(album, "audio_modes") or []

    return {
        **format_album_data(album),
        "version": safe_attr(album, "version"),
        "explicit": safe_attr(album, "explicit"),
        "copyright": safe_attr(album, "copyright"),
        "audio_quality": safe_attr(album, "audio_quality"),
        "audio_modes": audio_modes,
        "popularity": safe_attr(album, "popularity"),
        "tidal_release_date": tidal_release_date,
        "review": review,
    }


def format_track_detail_data(track) -> dict:
    """
    Format a track object with extended details.

    Extends format_track_data with additional metadata.

    Args:
        track: TIDAL track object

    Returns:
        Dictionary with detailed track information
    """
    tidal_release_date = safe_attr(track, "tidal_release_date")
    if tidal_release_date is not None:
        tidal_release_date = str(tidal_release_date)

    audio_modes = safe_attr(track, "audio_modes") or []

    return {
        **format_track_data(track),
        "isrc": safe_attr(track, "isrc"),
        "explicit": safe_attr(track, "explicit"),
        "track_num": safe_attr(track, "track_num"),
        "volume_num": safe_attr(track, "volume_num"),
        "version": safe_attr(track, "version"),
        "audio_quality": safe_attr(track, "audio_quality"),
        "audio_modes": audio_modes,
        "copyright": safe_attr(track, "copyright"),
        "popularity": safe_attr(track, "popularity"),
        "tidal_release_date": tidal_release_date,
    }


def format_lyrics_data(lyrics) -> dict:
    """
    Format a Lyrics object into a standardized dictionary.

    Args:
        lyrics: TIDAL Lyrics object

    Returns:
        Dictionary with lyrics information
    """
    return {
        "text": safe_attr(lyrics, "text", ""),
        "subtitles": safe_attr(lyrics, "subtitles", ""),
        "provider": safe_attr(lyrics, "provider", ""),
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
    if hasattr(playlist, "creator") and playlist.creator:
        creator_name = safe_attr(playlist.creator, "name")

    return {
        "id": playlist.id,
        "title": safe_attr(playlist, "name"),
        "creator": creator_name,
        "track_count": safe_attr(playlist, "num_tracks", 0),
        "duration": safe_attr(playlist, "duration", 0),
        "url": tidal_playlist_url(playlist.id),
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
    if hasattr(video, "artist"):
        artist_name = safe_attr(video.artist, "name", "Unknown")

    return {
        "id": video.id,
        "title": safe_attr(video, "name"),
        "artist": artist_name,
        "duration": safe_attr(video, "duration"),
        "url": tidal_video_url(video.id),
    }


def get_entity_or_404(session, entity_type: str, entity_id: str):
    """
    Get a TIDAL entity or return None with a 404 error response.

    Args:
        session: Authenticated TIDAL session
        entity_type: Entity type name matching session method (e.g., "artist", "album", "track", "playlist")
        entity_id: The entity ID to fetch

    Returns:
        Tuple of (entity, None) if found, or (None, error_response) if not found
    """
    fetcher = getattr(session, entity_type, None)
    if not fetcher:
        return None, (jsonify({"error": f"Unknown entity type: {entity_type}"}), 400)

    entity = fetcher(entity_id)
    if not entity:
        return None, (jsonify({"error": f"{entity_type.capitalize()} with ID {entity_id} not found"}), 404)
    return entity, None


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
        operation: "add", "remove", "edit", "move", "clear", "merge", or "visibility"

    Returns:
        None if OK, or error response tuple if not a user playlist
    """
    method_map = {
        "add": "add",
        "remove": "remove_by_id",
        "edit": "edit",
        "move": "move_by_indices",
        "clear": "clear",
        "merge": "merge",
        "visibility": "set_playlist_public",
    }

    required_method = method_map.get(operation, "add")

    if not hasattr(playlist, required_method):
        return jsonify({"error": "Cannot modify this playlist - not a user playlist"}), 403

    return None


def format_mix_data(mix) -> dict:
    """
    Format a mix object into a standardized dictionary.

    Args:
        mix: TIDAL mix object

    Returns:
        Dictionary with standardized mix information
    """
    image_url = None
    if hasattr(mix, "image") and callable(mix.image):
        try:
            image_url = mix.image(640)
        except (ValueError, AttributeError):
            pass

    mix_type = safe_attr(mix, "mix_type")
    if mix_type is not None and hasattr(mix_type, "value"):
        mix_type = mix_type.value

    updated = safe_attr(mix, "updated")
    if updated is not None:
        updated = str(updated)

    return {
        "id": mix.id,
        "title": safe_attr(mix, "title"),
        "sub_title": safe_attr(mix, "sub_title"),
        "short_subtitle": safe_attr(mix, "short_subtitle"),
        "mix_type": mix_type,
        "image_url": image_url,
        "updated": updated,
    }


def format_mix_from_dict(mix_data: dict) -> dict:
    """Format a raw TIDAL API mix dict into the standard response shape.

    Produces the same output shape as format_mix_data() for object-based mixes.

    Args:
        mix_data: Raw mix dict from TIDAL API (id, title, subTitle, images, etc.)

    Returns:
        Standardized mix dict with id, title, sub_title, mix_type, image_url
    """
    images = mix_data.get("images") or {}
    image_url = None
    if images:
        medium = images.get("MEDIUM") or {}
        image_url = medium.get("url")

    return {
        "id": mix_data.get("id", ""),
        "title": mix_data.get("title"),
        "sub_title": mix_data.get("subTitle"),
        "short_subtitle": mix_data.get("shortSubtitle"),
        "mix_type": mix_data.get("mixType"),
        "image_url": image_url,
        "updated": None,  # Not available in raw API mix listings
    }


def format_page_link_data(page_link) -> dict:
    """
    Format a PageLink object into a standardized dictionary.

    Args:
        page_link: TIDAL PageLink object

    Returns:
        Dictionary with page link information
    """
    return {
        "title": safe_attr(page_link, "title"),
        "api_path": safe_attr(page_link, "api_path"),
        "icon": safe_attr(page_link, "icon"),
        "image_id": safe_attr(page_link, "image_id"),
    }


def format_page_item_data(page_item) -> dict:
    """
    Format a PageItem (featured item) into a standardized dictionary.

    Args:
        page_item: TIDAL PageItem object

    Returns:
        Dictionary with featured item information
    """
    return {
        "header": safe_attr(page_item, "header", ""),
        "short_header": safe_attr(page_item, "short_header", ""),
        "short_sub_header": safe_attr(page_item, "short_sub_header", ""),
        "type": safe_attr(page_item, "type", ""),
        "artifact_id": safe_attr(page_item, "artifact_id", ""),
        "featured": safe_attr(page_item, "featured", False),
    }


def format_genre_data(genre) -> dict:
    """
    Format a Genre object into a standardized dictionary.

    Args:
        genre: TIDAL Genre object

    Returns:
        Dictionary with genre information
    """
    return {
        "name": safe_attr(genre, "name", ""),
        "path": safe_attr(genre, "path", ""),
        "has_playlists": safe_attr(genre, "playlists", False),
        "has_artists": safe_attr(genre, "artists", False),
        "has_albums": safe_attr(genre, "albums", False),
        "has_tracks": safe_attr(genre, "tracks", False),
        "has_videos": safe_attr(genre, "videos", False),
        "image": safe_attr(genre, "image", ""),
    }


# Map type names to their formatter functions
_PAGE_ITEM_FORMATTERS: dict[str, Any] = {
    "Artist": format_artist_data,
    "Album": format_album_data,
    "Track": format_track_data,
    "Playlist": format_playlist_search_data,
    "UserPlaylist": format_user_playlist_data,
    "Video": format_video_data,
    "Mix": format_mix_data,
    "PageLink": format_page_link_data,
    "PageItem": format_page_item_data,
}


def _format_page_category_item(item) -> dict | None:
    """
    Detect item type and delegate to the correct formatter.

    Uses exact type name match first, then falls back to suffix matching
    to handle subclasses (e.g., FeaturedAlbum → Album).

    Args:
        item: A TIDAL page category item (Artist, Album, Track, etc.)

    Returns:
        Dict with {type, data} or None if the type is not supported
    """
    type_name = type(item).__name__
    formatter = _PAGE_ITEM_FORMATTERS.get(type_name)
    if not formatter:
        for key, fmt in _PAGE_ITEM_FORMATTERS.items():
            if type_name.endswith(key):
                formatter = fmt
                type_name = key
                break
    if formatter:
        return {"type": type_name.lower(), "data": formatter(item)}
    return None


def serialize_page_categories(page) -> list[dict]:
    """
    Serialize a TIDAL Page's categories into a list of dicts.

    Iterates page.categories, formats each item using existing formatters,
    and skips TextBlock/LinkList categories.

    Args:
        page: TIDAL Page object

    Returns:
        List of {title, items: [{type, data}], count} dicts
    """
    categories = safe_attr(page, "categories") or []
    result = []

    for category in categories:
        type_name = type(category).__name__
        if type_name in ("TextBlock", "LinkList"):
            continue

        title = safe_attr(category, "title", "")
        raw_items = safe_attr(category, "items") or []

        formatted_items = []
        for item in raw_items:
            formatted = _format_page_category_item(item)
            if formatted:
                formatted_items.append(formatted)

        result.append(
            {
                "title": title,
                "items": formatted_items,
                "count": len(formatted_items),
            }
        )

    return result
