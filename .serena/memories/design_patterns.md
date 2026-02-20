# Design Patterns

## 1. Formatter Pattern

Formatters transform tidalapi objects into JSON-serializable dictionaries.

**Base Formatters**: Essential fields only
```python
def format_track_data(track: tidalapi.Track) -> dict:
    """Format track data with essential fields."""
    return {
        "id": track.id,
        "name": track.name,
        "duration": track.duration,
        "artist": safe_attr(track, "artist.name", "Unknown Artist"),
    }
```

**Detail Formatters**: Extend base via dict spread
```python
def format_track_detail(track: tidalapi.Track) -> dict:
    """Format track data with additional details."""
    base = format_track_data(track)
    return {
        **base,
        "album": safe_attr(track, "album.name", "Unknown Album"),
        "isrc": track.isrc,
        "explicit": track.explicit,
    }
```

**Use `safe_attr()` for nested attributes** to avoid AttributeError:
```python
artist_name = safe_attr(track, "artist.name", "Unknown Artist")
album_id = safe_attr(track, "album.id", None)
```

**Use try/except for `.image()` method calls** (can fail for missing images):
```python
try:
    image_url = artist.image(320)
except Exception:
    image_url = None
```

---

## 2. Flask Endpoint Pattern

All Flask endpoints follow this decorator pattern for auth and error handling.

```python
@blueprint.route("/endpoint/<id>")
@requires_tidal_auth          # 1. Check OAuth session first
@handle_endpoint_errors("fetch entity")  # 2. Catch and format errors
def get_endpoint(id: str):
    # 3. Get session
    session = get_tidal_session()
    
    # 4. Fetch entity with 404 handling
    entity = get_entity_or_404(
        fetch_fn=lambda: session.track(id),
        entity_type="Track",
        entity_id=id
    )
    
    # 5. Format and return
    return jsonify(format_track_detail(entity))
```

**Key Points:**
- `@requires_tidal_auth`: Returns 401 if no session file exists
- `@handle_endpoint_errors("action")`: Catches exceptions, returns 500 with error message
- `get_entity_or_404()`: Returns 404 if entity not found, 500 for other errors
- Always use `jsonify()` for JSON responses

---

## 3. MCP Tool Pattern

MCP tools call Flask endpoints over HTTP and handle errors.

```python
@server.tool()
async def get_track(track_id: str) -> dict:
    """Get track by ID."""
    # 1. Check auth first
    check_tidal_auth()
    
    # 2. Validate inputs
    validate_track_id(track_id)
    
    # 3. Call Flask endpoint via HTTP
    return mcp_get(f"/tracks/{track_id}")
```

**Helper Functions:**
- `check_tidal_auth()`: Raises error if auth check fails (HTTP GET /auth/status)
- `validate_*()`: Validates input parameters (ID format, limit ranges, etc.)
- `mcp_get(endpoint, params={})`: HTTP GET to Flask with error handling
- `mcp_post(endpoint, json={})`: HTTP POST to Flask with error handling
- `mcp_delete(endpoint)`: HTTP DELETE to Flask with error handling

**Key Points:**
- Always call `check_tidal_auth()` BEFORE any API calls
- Validate inputs before making HTTP requests
- Use `mcp_get/post/delete()` helpers (they handle timeouts and exceptions)
- Catch `requests.RequestException`, not bare `Exception`

---

## 4. Testing Pattern

One test class per endpoint/tool with standard coverage.

**Flask Endpoint Tests:**
```python
class TestGetTrack:
    def test_get_track_success(self, client, mock_session_file):
        # Mock tidalapi method
        with patch("tidal_api.browser_session.get_tidal_session") as mock_session:
            mock_track = MockTrack(id="123", name="Song")
            mock_session.return_value.track.return_value = mock_track
            
            # Call endpoint
            response = client.get("/tracks/123")
            
            # Assert
            assert response.status_code == 200
            assert response.json["name"] == "Song"
    
    def test_get_track_not_found(self, client, mock_session_file):
        with patch("tidal_api.browser_session.get_tidal_session") as mock_session:
            mock_session.return_value.track.return_value = None
            
            response = client.get("/tracks/999")
            assert response.status_code == 404
    
    def test_get_track_not_authenticated(self, client):
        # No mock_session_file = no auth
        response = client.get("/tracks/123")
        assert response.status_code == 401
```

**MCP Tool Tests:**
```python
class TestGetTrack:
    def test_get_track_success(self, mock_auth_success):
        # Mock HTTP response from Flask
        with patch("mcp_server.utils.mcp_get") as mock_get:
            mock_get.return_value = {"id": "123", "name": "Song"}
            
            # Call tool
            result = asyncio.run(get_track("123"))
            
            # Assert
            assert result["name"] == "Song"
            mock_get.assert_called_once_with("/tracks/123")
    
    def test_get_track_not_authenticated(self, mock_auth_failure):
        # Auth check fails
        with pytest.raises(Exception, match="Not authenticated"):
            asyncio.run(get_track("123"))
```

**Standard Coverage:**
- ✅ Success case (200, valid response)
- ✅ Not found case (404)
- ✅ Not authenticated case (401)
- Optional: Invalid input, rate limits, timeouts

---

## 5. Error Handling Pattern

**Flask Routes:**
```python
@blueprint.route("/endpoint")
@handle_endpoint_errors("fetch data")  # Decorator handles all exceptions
def endpoint():
    # Don't catch exceptions here - let decorator handle it
    data = some_operation()
    return jsonify(data)
```

**MCP Tools:**
```python
@server.tool()
async def tool_name(param: str) -> dict:
    check_tidal_auth()  # Raises exception if not authenticated
    
    try:
        return mcp_get(f"/endpoint/{param}")
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data: {e}", exc_info=True)
        raise McpError(f"Failed to fetch data: {str(e)}")
```

**Logging:**
```python
# Always use logging.error with exc_info=True
try:
    risky_operation()
except SomeException as e:
    logging.error(f"Operation failed: {e}", exc_info=True)
    raise
```

---

## 6. tidalapi Reference Patterns

**Image URLs:**
```python
# artist.image(dim) is a METHOD (returns URL)
artist_image = artist.image(320)  # Valid dims: 160, 320, 480, 750

# artist.picture is a STRING (UUID attribute)
picture_uuid = artist.picture

# album.image(dim) is also a METHOD
album_image = album.image(640)  # Valid dims: 80, 160, 320, 640, 1280
```

**Method Signatures:**
```python
# get_radio() and get_similar() take NO arguments
radio_tracks = artist.get_radio()  # NO limit parameter
similar_artists = artist.get_similar()  # NO limit parameter

# get_top_tracks() accepts limit and offset
top_tracks = artist.get_top_tracks(limit=10, offset=0)  # None limit = 1000 default
```

**Search Results:**
```python
# session.search() returns a TypedDict (dict), NOT an object
results = session.search("query")

# Use .get() with default, NOT attribute access
tracks = results.get("tracks", [])  # ✅ Correct
tracks = results.tracks  # ❌ AttributeError
```

**Verification:**
Always check installed library source for ground truth:
```bash
# View tidalapi source
ls .venv/lib/python3.10/site-packages/tidalapi/

# Read artist.py for Artist class methods
cat .venv/lib/python3.10/site-packages/tidalapi/artist.py
```

---

## 7. Pagination Pattern

**Fetch All Pages:**
```python
from tidal_api.utils import fetch_all_paginated

# Fetch all results across multiple pages
all_items = fetch_all_paginated(
    fetch_fn=artist.get_top_tracks,  # Pass method directly (no lambda)
    limit=50,                         # Page size
    max_pages=None                    # None = fetch all
)
```

**Key Points:**
- `fetch_all_paginated` calls `fetch_fn(limit=..., offset=...)` with keyword args
- Pass tidalapi methods directly (e.g., `artist.get_top_tracks`)
- Don't wrap in lambda unless you need to bind other arguments
- Set `max_pages` to limit total pages fetched (None = fetch all)
