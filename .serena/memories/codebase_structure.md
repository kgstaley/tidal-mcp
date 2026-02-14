# Codebase Structure

```
tidal-mcp/
├── tidal_api/              # Flask backend (HTTP server on port 5050)
│   ├── routes/             # Flask blueprints (one per domain)
│   │   ├── auth.py         # Authentication endpoints (login, status)
│   │   ├── tracks.py       # Track operations (get, recommendations)
│   │   ├── playlists.py    # Playlist CRUD (create, update, delete, reorder)
│   │   ├── favorites.py    # Favorites management (add/remove tracks, albums, artists)
│   │   ├── search.py       # Catalog search (tracks, albums, artists, videos)
│   │   ├── discovery.py    # Discovery features (recommendations, mixes)
│   │   ├── mixes.py        # Mix operations (get, fetch items)
│   │   ├── artists.py      # Artist operations (get, top tracks, radio, similar)
│   │   └── albums.py       # Album operations (get, fetch items)
│   ├── app.py              # Flask app factory (creates Flask instance)
│   ├── utils.py            # Shared formatters, helpers, constants
│   │                       # - format_track_data(), format_artist_data(), etc.
│   │                       # - safe_attr(), DEFAULT_LIMIT, MAX_LIMIT
│   └── browser_session.py  # OAuth browser flow (get_tidal_session)
│
├── mcp_server/             # MCP stdio interface (Claude integration)
│   ├── tools/              # MCP tool modules (one per domain, matches routes/)
│   │   ├── auth.py         # Authentication tools
│   │   ├── tracks.py       # Track tools
│   │   ├── playlists.py    # Playlist tools
│   │   ├── favorites.py    # Favorites tools
│   │   ├── search.py       # Search tools
│   │   ├── discovery.py    # Discovery tools
│   │   ├── mixes.py        # Mix tools
│   │   ├── artists.py      # Artist tools
│   │   └── albums.py       # Album tools
│   ├── server.py           # MCP server entrypoint (starts Flask subprocess)
│   ├── mcp_app.py          # MCP app configuration (tool registration)
│   └── utils.py            # MCP-side validation, HTTP helpers, error handling
│                           # - check_tidal_auth(), validate_*(), mcp_get/post/delete()
│
├── tests/                  # Nested test modules mirroring source layout
│   ├── conftest.py         # Shared mock classes (MockArtist, MockTrack, MockAlbum, etc.)
│   ├── tidal_api/          # Flask backend tests
│   │   ├── conftest.py     # Flask fixtures (client, mock_session_file)
│   │   ├── test_auth.py    # Test /auth/* endpoints
│   │   ├── test_tracks.py  # Test /tracks/* endpoints
│   │   ├── test_playlists.py
│   │   ├── test_favorites.py
│   │   ├── test_search.py
│   │   ├── test_discovery.py
│   │   ├── test_mixes.py
│   │   ├── test_artists.py
│   │   └── test_albums.py
│   └── mcp_server/         # MCP tools tests
│       ├── conftest.py     # MCP fixtures (mock HTTP responses, NOT Flask)
│       ├── test_auth.py    # Test auth tools
│       ├── test_tracks.py  # Test track tools
│       └── ...             # (same structure as tidal_api tests)
│
├── docs/
│   ├── patterns.md         # Implementation patterns reference (formatter, Flask, MCP, testing)
│   └── CHANGELOG.md        # Version history and changes
│
├── .serena/
│   ├── project.yml         # LSP configuration (Python LSP)
│   └── memories/           # Persistent memory files (this file is one of them)
│
├── pyproject.toml          # Python project config (dependencies, ruff settings)
├── CLAUDE.md               # Project-specific documentation for Claude
├── README.md               # Project overview and setup instructions
└── .python-version         # Python version (3.10)
```

## Key Directories

### `tidal_api/routes/`
Flask blueprints implementing REST endpoints. Each file corresponds to a domain (auth, tracks, playlists, etc.).

**Pattern:**
- One blueprint per domain
- Endpoints use `@requires_tidal_auth` decorator for session verification
- Endpoints use `@handle_endpoint_errors("action")` decorator for error handling
- Use `get_entity_or_404()` helper for fetching entities with 404 handling

### `mcp_server/tools/`
MCP tool modules that call Flask endpoints over HTTP. Structure mirrors `tidal_api/routes/`.

**Pattern:**
- One tool module per domain (matches route structure)
- Tools use `check_tidal_auth()` before API calls
- Tools use `validate_*()` for input validation
- Tools use `mcp_get/post/delete()` helpers for HTTP requests to Flask

### `tests/`
Test modules mirror the source layout. Flask tests in `tidal_api/`, MCP tests in `mcp_server/`.

**Shared Mocks (tests/conftest.py):**
- `MockArtist`, `MockAlbum`, `MockTrack`, `MockVideo`
- `MockCreator`, `MockPlaylist`, `MockUserPlaylist`
- `MockResponse` (for HTTP mocking)

**Flask Fixtures (tests/tidal_api/conftest.py):**
- `client` - Flask test client
- `mock_session_file` - Mock OAuth session file

**MCP Fixtures (tests/mcp_server/conftest.py):**
- `mock_auth_success` - Mock successful HTTP auth check
- `mock_auth_failure` - Mock failed HTTP auth check

## File Naming Conventions
- Route files: `tidal_api/routes/<domain>.py`
- Tool files: `mcp_server/tools/<domain>.py`
- Test files: `tests/<package>/test_<domain>.py`
- Utility files: `<package>/utils.py`
- Configuration: `pyproject.toml`, `.serena/project.yml`
