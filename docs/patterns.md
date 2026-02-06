# Implementation Patterns

Guide to established code patterns in the TIDAL MCP project. Use these patterns for consistency when adding new features.

## Table of Contents

- [Formatter Pattern](#formatter-pattern)
- [Flask Endpoint Pattern](#flask-endpoint-pattern)
- [MCP Tool Pattern](#mcp-tool-pattern)
- [Testing Pattern](#testing-pattern)
- [Error Handling](#error-handling)
- [tidalapi Common Patterns](#tidalapi-common-patterns)

---

## Formatter Pattern

**What it is**: Formatters convert tidalapi objects into standardized JSON dictionaries for API responses. Base formatters provide core fields, while detail formatters extend them with additional metadata.

**When to use**: Every Flask endpoint that returns tidalapi objects (artists, albums, tracks, etc.) should use a formatter to ensure consistent response structure.

### Base Formatters

Base formatters provide essential fields for a resource:

```python
def format_artist_data(artist) -> dict:
    """
    Format an artist object into a standardized dictionary.

    Args:
        artist: TIDAL artist object

    Returns:
        Dictionary with standardized artist information
    """
    # Use safe image() method call with try/except
    picture_url = None
    if hasattr(artist, "image") and callable(artist.image):
        try:
            picture_url = artist.image(320)
        except ValueError:
            pass

    return {
        "id": artist.id,
        "name": artist.name,
        "picture_url": picture_url,
        "url": tidal_artist_url(artist.id),
    }
```

```python
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
        "artist": safe_attr(track.artist, "name", "Unknown"),  # Use safe_attr for nested attrs
        "album": safe_attr(track.album, "name", "Unknown"),
        "duration": safe_attr(track, "duration", 0),
        "url": tidal_track_url(track.id),
    }

    # Include optional fields only when provided
    if source_track_id:
        track_data["source_track_id"] = source_track_id

    return track_data
```

### Detail Formatters

Detail formatters extend base formatters using dict spread (`{**base, ...}`):

```python
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
    # Extract roles and convert enum values to strings
    raw_roles = safe_attr(artist, "roles") or []
    roles = [r.value if hasattr(r, "value") else str(r) for r in raw_roles]

    # Extend base formatter with additional fields
    return {
        **format_artist_data(artist),
        "bio": bio,
        "roles": roles,
    }
```

```python
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
    # Convert datetime to string if present
    tidal_release_date = safe_attr(album, "tidal_release_date")
    if tidal_release_date is not None:
        tidal_release_date = str(tidal_release_date)

    # Handle list attributes with fallback to empty list
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
```

### Best Practices

- **Use `safe_attr()`** for optional fields to avoid AttributeError
- **Convert enums to strings** via `.value` for JSON serialization
- **Convert datetime to str** if not None (e.g., `str(release_date)`)
- **Fallback lists to `[]`** for missing list attributes (e.g., `audio_modes or []`)
- **Detail formatters extend base** via dict spread pattern: `{**format_base(obj), ...}`
- **Handle nested objects safely** with `safe_attr(obj.nested, "field", default)`

### Common Pitfalls

- **Don't assume attributes exist** — tidalapi objects vary by API response
- **Don't call `.value` on non-enum objects** — check `hasattr(obj, "value")` first
- **Don't forget to convert datetime** — JSON serialization requires strings

---

## Flask Endpoint Pattern

**What it is**: Flask endpoints follow a consistent decorator stack and error handling pattern. All endpoints require authentication and handle errors uniformly.

**When to use**: Every Flask route that accesses TIDAL data should follow this pattern.

### Decorator Stack

Endpoints use two decorators in this order:

```python
from tidal_api.utils import (
    get_entity_or_404,
    handle_endpoint_errors,
    requires_tidal_auth,
)

@artists_bp.route("/api/artists/<artist_id>", methods=["GET"])
@requires_tidal_auth  # First: Check auth, inject session kwarg
@handle_endpoint_errors("fetching artist info")  # Second: Catch exceptions, return 500
def get_artist(artist_id: str, session):
    """Get detailed information about an artist."""
    # 1. Look up the resource
    artist, error = get_entity_or_404(session, "artist", artist_id)
    if error:
        return error

    # 2. Fetch optional data with exception handling
    bio = None
    try:
        bio = artist.get_bio()
    except Exception:
        logger.debug("Bio not available for artist %s", artist_id)

    # 3. Format and return response
    return jsonify(format_artist_detail_data(artist, bio=bio))
```

### Entity Lookups

Use `get_entity_or_404()` for consistent not-found handling:

```python
@artists_bp.route("/api/artists/<artist_id>/top-tracks", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist top tracks")
def get_artist_top_tracks(artist_id: str, session):
    """Get an artist's top tracks."""
    # Lookup returns (entity, None) if found, or (None, error_response) if not
    artist, error = get_entity_or_404(session, "artist", artist_id)
    if error:
        return error

    # Parse query params with defaults
    limit = bound_limit(request.args.get("limit", default=20, type=int))

    # Call tidalapi method
    tracks = artist.get_top_tracks(limit=limit)
    track_list = [format_track_data(t) for t in tracks]

    # Return consistent response structure
    return jsonify({
        "artist_id": artist_id,
        "tracks": track_list,
        "total": len(track_list),
    })
```

### Pagination Pattern

Use `fetch_all_paginated()` for endpoints that need to batch requests:

```python
from tidal_api.utils import fetch_all_paginated, bound_limit

@artists_bp.route("/api/artists/<artist_id>/albums", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist albums")
def get_artist_albums(artist_id: str, session):
    """Get an artist's albums."""
    artist, error = get_entity_or_404(session, "artist", artist_id)
    if error:
        return error

    # Parse query params
    album_filter = request.args.get("filter", "albums")
    limit = bound_limit(request.args.get("limit", default=50, type=int))

    # Map filter param to tidalapi method name
    filter_method_names = {
        "albums": "get_albums",
        "ep_singles": "get_ep_singles",
        "other": "get_other",
    }

    method_name = filter_method_names.get(album_filter)
    if not method_name:
        return jsonify({"error": f"Invalid filter: {album_filter}. Use: albums, ep_singles, other"}), 400

    # Get the method and fetch with pagination
    fetch_fn = getattr(artist, method_name)
    albums = fetch_all_paginated(fetch_fn, limit=limit)
    album_list = [format_album_data(a) for a in albums]

    return jsonify({
        "artist_id": artist_id,
        "filter": album_filter,
        "albums": album_list,
        "total": len(album_list),
    })
```

### Best Practices

- **Decorator order matters**: `@requires_tidal_auth` first, then `@handle_endpoint_errors()`
- **Always use `get_entity_or_404()`** for resource lookups — provides consistent error responses
- **Parse query params with defaults** using `request.args.get("param", default=value, type=int)`
- **Bound limits** with `bound_limit()` to prevent excessive requests
- **Use formatters** for all response data — never return raw tidalapi objects
- **Return consistent JSON structure** with resource ID and total count
- **Handle optional data** with try/except, log with `logger.debug()` when not available

### Common Pitfalls

- **Don't swap decorator order** — auth must happen before error handling
- **Don't return raw tidalapi objects** — always use formatters
- **Don't forget timeout parameters** when calling tidalapi methods that support them
- **Don't assume all tidalapi methods accept pagination** — verify in the library source

---

## MCP Tool Pattern

**What it is**: MCP tools follow a strict validation flow: check auth → validate inputs → call HTTP helper → handle response.

**When to use**: Every MCP tool that calls the Flask backend should follow this pattern.

### Tool Structure

```python
import logging
import requests
from server import mcp
from utils import (
    check_tidal_auth,
    error_response,
    mcp_get,
    validate_string,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_artist_info(artist_id: str) -> dict:
    """
    Get detailed information about a TIDAL artist including bio and roles.

    USE THIS TOOL WHEN A USER ASKS FOR:
    - "Tell me about [artist name]"
    - "Who is [artist name]?"
    - "Get info on [artist]"
    - "What do you know about [artist] on TIDAL?"

    The user must be authenticated with TIDAL first.

    Args:
        artist_id: The TIDAL artist ID (required)

    Returns:
        A dictionary containing artist details: name, bio, roles, picture URL, and TIDAL URL
    """
    # Step 1: Check authentication
    auth_error = check_tidal_auth("get artist info")
    if auth_error:
        return auth_error

    # Step 2: Validate required inputs
    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    # Step 3: Call Flask endpoint via HTTP helper
    try:
        data = mcp_get(f"/api/artists/{artist_id}", "artist", resource_id=artist_id)
        if data.get("status") == "error":
            return data

        # Step 4: Return success response
        return {"status": "success", **data}

    # Step 5: Handle request exceptions
    except requests.RequestException as e:
        logger.error("Failed to fetch artist info", exc_info=True)
        return error_response(f"Failed to fetch artist info: {e}")
```

### Validation Flow

```python
@mcp.tool()
def get_artist_albums(artist_id: str, filter: str = "albums", limit: int = 50) -> dict:
    """
    Get an artist's albums, EPs/singles, or other releases on TIDAL.

    Args:
        artist_id: The TIDAL artist ID (required)
        filter: Type of releases — "albums", "ep_singles", or "other" (default: "albums")
        limit: Maximum number of albums to return (default: 50)

    Returns:
        A dictionary containing the artist's albums/releases
    """
    # Always check auth first
    auth_error = check_tidal_auth("get artist albums")
    if auth_error:
        return auth_error

    # Validate required string inputs
    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    # Call Flask endpoint with params
    try:
        data = mcp_get(
            f"/api/artists/{artist_id}/albums",
            "artist",
            params={"filter": filter, "limit": limit},  # Query params as dict
            resource_id=artist_id,
        )
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    except requests.RequestException as e:
        logger.error("Failed to fetch artist albums", exc_info=True)
        return error_response(f"Failed to fetch artist albums: {e}")
```

### HTTP Helpers

Use `mcp_get()`, `mcp_post()`, `mcp_delete()` for Flask API calls:

```python
# GET request with query params
data = mcp_get(
    f"/api/artists/{artist_id}/top-tracks",
    "artist",
    params={"limit": limit},
    resource_id=artist_id,
)

# POST request with JSON body
data = mcp_post(
    f"/api/playlists/{playlist_id}/tracks",
    "playlist",
    payload={"track_ids": track_ids},
    resource_id=playlist_id,
)

# DELETE request with JSON body
data = mcp_delete(
    f"/api/playlists/{playlist_id}/tracks",
    "playlist",
    payload={"track_ids": track_ids},
    resource_id=playlist_id,
)
```

### Best Practices

- **Validation order**: auth check → input validation → HTTP call
- **Use `check_tidal_auth(action)`** with descriptive action string
- **Use `validate_string()`** for required string inputs (IDs, names)
- **Use `validate_list()`** for required list inputs (track_ids, etc.)
- **Catch `requests.RequestException`** specifically, not bare `Exception`
- **Log errors with `exc_info=True`** for full tracebacks
- **Always check `data.get("status")`** after HTTP helpers return
- **Include "USE THIS TOOL WHEN" section** in docstrings with example user queries

### Common Pitfalls

- **Don't skip auth check** — every tool must verify authentication
- **Don't catch bare `Exception`** — catch `requests.RequestException` only
- **Don't forget resource_id parameter** — improves error messages
- **Don't assume HTTP call succeeded** — always check for error status

---

## Testing Pattern

**What it is**: Tests follow a consistent structure with one test class per endpoint/tool, using shared mock classes and fixtures.

**When to use**: Every new Flask endpoint and MCP tool must have corresponding tests.

### Flask Tests

Flask tests use the `client` fixture and mock the tidalapi session:

```python
"""Tests for /api/artists Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockAlbum, MockArtist, MockTrack


class TestGetArtist:
    """Tests for GET /api/artists/<id> endpoint."""

    def test_get_artist_success(self, client, mock_session_file, mocker):
        """Test successfully fetching artist info."""
        from enum import Enum

        # Define mock enum for roles
        class MockRole(Enum):
            main = "MAIN"
            featured = "FEATURED"

        # Create mock session and configure responses
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist(id=123, name="Test Artist")
        mock_artist.roles = [MockRole.main, MockRole.featured]
        mock_artist.get_bio = MagicMock(return_value="A great artist biography.")
        mock_session.artist.return_value = mock_artist

        # Patch the session factory
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        # Make request and assert response
        response = client.get("/api/artists/123")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["id"] == 123
        assert data["name"] == "Test Artist"
        assert data["bio"] == "A great artist biography."
        assert data["roles"] == ["MAIN", "FEATURED"]
        assert "url" in data
        assert "picture_url" in data

    def test_get_artist_not_found(self, client, mock_session_file, mocker):
        """Test fetching non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None  # Not found
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999")
        assert response.status_code == 404

    def test_get_artist_not_authenticated(self, client):
        """Test fetching artist when not authenticated."""
        # No mock_session_file fixture = not authenticated
        response = client.get("/api/artists/123")
        assert response.status_code == 401
```

### MCP Tests

MCP tests mock HTTP responses via `mcp_utils_real.http`:

```python
"""Tests for artist MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetArtistInfo:
    """Tests for get_artist_info MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting artist info when not authenticated."""
        from tools.artists import get_artist_info

        result = get_artist_info("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_artist_id(self, mocker):
        """Test with empty artist ID."""
        # Mock successful auth check
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.artists import get_artist_info

        result = get_artist_info("")

        assert result["status"] == "error"
        assert "artist ID" in result["message"]

    def test_success(self, mocker):
        """Test successfully getting artist info."""
        artist_data = {
            "id": 123,
            "name": "Test Artist",
            "bio": "A great artist.",
            "roles": ["Main Artist"],
            "picture_url": "https://example.com/pic.jpg",
            "url": "https://tidal.com/browse/artist/123",
        }

        # Mock HTTP responses for auth check and API call
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/artists/123" in url:
                return MockResponse(artist_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_info

        result = get_artist_info("123")

        assert result["status"] == "success"
        assert result["name"] == "Test Artist"
        assert result["bio"] == "A great artist."

    def test_artist_not_found(self, mocker):
        """Test getting info for non-existent artist."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_info

        result = get_artist_info("999")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
```

### Coverage Requirements

Every endpoint/tool must have these test cases:

1. **Success case** — Valid inputs, successful response
2. **Not found** — Resource doesn't exist (404)
3. **Not authenticated** — No auth token (401)
4. **Invalid inputs** — Empty strings, invalid parameters
5. **Edge cases** — Optional data missing, pagination limits, etc.

### Best Practices

- **One test class per endpoint/tool** with descriptive class name
- **Use shared mock classes** from `tests/conftest.py` (MockArtist, MockAlbum, etc.)
- **Flask fixtures**: `client`, `mock_session_file` from `tests/tidal_api/conftest.py`
- **MCP fixtures**: `mock_auth_failure`, `mock_auth_success` from `tests/mcp_server/conftest.py`
- **Descriptive test names** following pattern `test_<scenario>` (e.g., `test_get_artist_not_found`)
- **Mock at the right level**: Flask tests mock session, MCP tests mock HTTP
- **Assert both status code and response data** in success cases
- **Use `side_effect`** for multi-call mocking (auth check + API call)

### Common Pitfalls

- **Don't mock too high** — Flask tests mock the session, not the endpoint
- **Don't mock too low** — MCP tests mock HTTP responses, not internal functions
- **Don't forget edge cases** — test missing optional data, empty results, etc.
- **Don't skip not_authenticated tests** — auth is critical to verify

---

## Error Handling

**What it is**: Consistent error handling across Flask endpoints and MCP tools using specific exceptions and logging.

**When to use**: All error paths in endpoints and tools should follow these patterns.

### Flask Error Handling

```python
@artists_bp.route("/api/artists/<artist_id>", methods=["GET"])
@requires_tidal_auth
@handle_endpoint_errors("fetching artist info")  # Catches all exceptions, returns 500
def get_artist(artist_id: str, session):
    """Get detailed information about an artist."""
    # Use get_entity_or_404 for consistent 404 responses
    artist, error = get_entity_or_404(session, "artist", artist_id)
    if error:
        return error  # Returns (jsonify({...}), 404) tuple

    # Handle optional data that might not be available
    bio = None
    try:
        bio = artist.get_bio()
    except Exception:
        # Log at debug level when optional data is unavailable
        logger.debug("Bio not available for artist %s", artist_id)

    return jsonify(format_artist_detail_data(artist, bio=bio))
```

### MCP Error Handling

```python
from utils import check_tidal_auth, error_response, validate_string
import requests

@mcp.tool()
def get_artist_info(artist_id: str) -> dict:
    """Get detailed information about a TIDAL artist."""
    # Step 1: Auth check returns error dict or None
    auth_error = check_tidal_auth("get artist info")
    if auth_error:
        return auth_error

    # Step 2: Input validation returns error dict or None
    id_error = validate_string(artist_id, "artist ID")
    if id_error:
        return id_error

    # Step 3: HTTP call in try/except, catch specific exception
    try:
        data = mcp_get(f"/api/artists/{artist_id}", "artist", resource_id=artist_id)
        if data.get("status") == "error":
            return data

        return {"status": "success", **data}

    # Catch specific exception type, not bare Exception
    except requests.RequestException as e:
        # Log with exc_info=True for full traceback
        logger.error("Failed to fetch artist info", exc_info=True)
        return error_response(f"Failed to fetch artist info: {e}")
```

### Timeout Requirements

All HTTP requests must specify a timeout:

```python
from utils import DEFAULT_TIMEOUT

# In mcp_server/utils.py helpers
response = http.get(f"{FLASK_APP_URL}{endpoint}", params=params, timeout=DEFAULT_TIMEOUT)

# In direct HTTP calls
response = http.post(url, json=payload, timeout=30)
```

### Best Practices

- **Catch specific exceptions** — use `requests.RequestException`, `MetadataNotAvailable`, etc.
- **Never catch bare `Exception`** in MCP tools — breaks error propagation
- **Log errors with `exc_info=True`** for full traceback
- **Use `logger.debug()`** for expected missing data (bio, review, etc.)
- **Use `logger.error()`** for unexpected failures
- **Always specify `timeout`** on HTTP requests (default: 30 seconds)
- **Return error dicts** from MCP tools, not raising exceptions
- **Use `error_response()`** helper for consistent error format

### Common Pitfalls

- **Don't catch bare `Exception`** — be specific
- **Don't forget timeout parameter** — requests will hang indefinitely
- **Don't use `print()`** — always use the `logging` module
- **Don't raise exceptions in MCP tools** — return error dicts instead

---

## tidalapi Common Patterns

**What it is**: Best practices for working with the tidalapi v0.8.3 library based on verified behavior from the installed package source.

**When to use**: Whenever interacting with tidalapi objects or calling library methods.

### Method Signatures

Always verify method signatures against the library source (`.venv/lib/python3.10/site-packages/tidalapi/`):

```python
# Artist methods
artist.get_bio()                                  # NO params, returns str
artist.get_top_tracks(limit=None, offset=0)      # limit=None uses session default (1000)
artist.get_albums(limit=50, offset=0)            # Paginated
artist.get_similar()                              # NO params
artist.get_radio()                                # NO params, returns up to 100 tracks

# Album methods
album.tracks(limit=None, offset=0, sparse_album=False)  # Paginated, returns List[Track]
album.similar()                                   # NO params, raises MetadataNotAvailable if none
album.review()                                    # NO params, raises requests.HTTPError if none
album.image(dimensions=320)                       # Valid dims: 80, 160, 320, 640, 1280

# Track methods
track.lyrics()                                    # NO params, raises MetadataNotAvailable if none
# Track has NO image() method — use album.image() instead

# Session methods
session.search(query, models=[Track, Album, Artist])  # Returns dict, not object
session.mixes()                                   # Returns Page object with .categories list
```

### Image URLs

```python
# Artist images — valid dimensions: 160, 320, 480, 750
picture_url = artist.image(320)  # artist.picture is UUID string, not URL

# Album images — valid dimensions: 80, 160, 320, 640, 1280
cover_url = album.image(640)

# Mix images — valid dimensions: 320, 640, 1500
mix_image_url = mix.image(640)

# Tracks have NO image() method — use album.image() instead
```

### Enum Handling

```python
# Roles are enum objects — serialize via .value
raw_roles = safe_attr(artist, "roles") or []
roles = [r.value if hasattr(r, "value") else str(r) for r in raw_roles]

# Mix types are enums
mix_type = mix.mix_type.value if hasattr(mix.mix_type, "value") else str(mix.mix_type)
```

### Exception Handling

```python
from tidalapi.exceptions import MetadataNotAvailable
import requests

# Album review may not exist
try:
    review = album.review()
except requests.HTTPError:
    review = None

# Similar albums may not exist
try:
    similar = album.similar()
except MetadataNotAvailable:
    similar = []

# Track lyrics may not exist
try:
    lyrics = track.lyrics()
except MetadataNotAvailable:
    lyrics = None
```

### Pagination

```python
from tidal_api.utils import fetch_all_paginated

# Use helper for methods that support limit/offset
albums = fetch_all_paginated(artist.get_albums, limit=100)

# Helper calls the method as: fetch_fn(limit=batch_size, offset=offset)
# Pass the method directly, no lambda wrapper needed
```

### Search Results

```python
# session.search() returns a dict, not an object
results = session.search("query", models=[Track, Album, Artist])

# Access results via dict keys, not attributes
tracks = results.get("tracks", [])
albums = results.get("albums", [])
artists = results.get("artists", [])
```

### Best Practices

- **Always check `.venv/lib/python3.10/site-packages/tidalapi/`** for ground truth on method signatures
- **Don't guess method parameters** — verify in the source
- **Use `safe_attr()`** for all optional attributes
- **Convert enums via `.value`** before JSON serialization
- **Convert datetime to str** before returning in API responses
- **Handle specific exceptions** (`MetadataNotAvailable`, `requests.HTTPError`)
- **Use `fetch_all_paginated`** for consistent pagination

### Common Pitfalls

- **Don't confuse `artist.image()` (method) with `artist.picture` (UUID string)**
- **Don't assume all methods accept parameters** — many take NO args (get_radio, get_similar, etc.)
- **Don't assume track has image()** — use album.image() instead
- **Don't use `results.tracks`** on search results — use `results.get("tracks", [])`
- **Don't forget to serialize enums** — JSON can't handle enum objects directly
