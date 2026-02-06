# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **PKCE auth flow for personal TIDAL developer credentials** — When `TIDAL_CLIENT_ID` is set, authentication uses the PKCE browser redirect flow instead of the device code flow. The login endpoint opens the browser, TIDAL redirects to a local `/api/auth/callback` endpoint, and tokens are exchanged automatically. The MCP tool polls `/api/auth/status` until auth completes.
- **`/api/auth/callback` endpoint** — Handles the TIDAL PKCE redirect, exchanges the authorization code for tokens, saves the session, and returns an HTML success page
- **`TIDAL_REDIRECT_URI` env var** — Optional override for the PKCE redirect URI (default: `http://localhost:{port}/api/auth/callback`)
- 17 new auth tests (12 Flask + 5 MCP) covering PKCE flow, callback, polling, and error cases

### Fixed
- **MCP server double module loading** — `mcp run` loaded `server.py` under a synthetic module name (`server_module`), causing tool files to re-import it as `server` and create a second `FastMCP` instance with zero tools. Extracted the `FastMCP` instance into `mcp_server/mcp_app.py` so all modules share one instance.
- **Flask subprocess failing to start** — The subprocess inherited Claude Desktop's working directory (not the project root), so `uv run` couldn't find `pyproject.toml` and `tidal_api` imports failed silently. Added `cwd=PROJECT_ROOT` and `stderr=sys.stderr` to `Popen`.
- **Port conflict on Flask reload** — `debug=True` caused Flask's stat reloader to fork and re-bind the port, crashing with "Address already in use". Disabled debug mode for subprocess usage.
- **Orphaned Flask process on MCP restart** — `atexit` handlers don't fire on `SIGTERM` (how Claude Desktop stops servers). Added signal handlers for `SIGTERM`/`SIGINT` to ensure Flask is terminated.
- **TIDAL `invalid_client` auth failure** — `tidalapi` v0.8.3's hardcoded OAuth client ID was revoked by TIDAL. Bumped to v0.8.11 with updated credentials.

### Added
- **Configurable OAuth credentials** — `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET` env vars override `tidalapi`'s built-in credentials, avoiding breakage when TIDAL revokes them
- **Flask startup health check** — `wait_for_flask()` polls the Flask backend after launch to confirm it's ready before the MCP server accepts tool calls
- **`.env.example`** — template for all supported environment variables

### Changed
- `tidalapi` minimum version bumped from 0.8.3 to 0.8.11
- MCP tool modules import `mcp` from `mcp_app` instead of `server`
- All MCP server logging explicitly directed to `stderr` (stdout reserved for JSON-RPC)

### Added

#### Phase 4: Full Favorites CRUD
- **Favorites tools** — 3 new MCP tools for managing favorites across all content types:
  - `get_favorites(type, limit, order, order_direction)` — retrieve favorite artists, albums, tracks, videos, playlists, or mixes
  - `add_favorite(type, id)` — add an item to favorites (artists, albums, tracks, videos, playlists)
  - `remove_favorite(type, id)` — remove an item from favorites
- 3 new Flask endpoints: `GET/POST/DELETE /api/favorites/<type>` with type dispatch tables
- 6 supported content types: artists, albums, tracks, videos, playlists (full CRUD) + mixes (read-only)
- Type dispatch pattern using lookup dicts for method/formatter/pagination routing
- `MockFavorites` test class with all 16 methods (5 list + 5 add + 5 remove + mixes)
- 39 new tests (24 Flask + 15 MCP)
- Existing `GET /api/tracks` endpoint preserved (no breaking change)

#### Phase 6: Discovery & Browsing
- **Discovery tools** — 6 new MCP tools for browsing TIDAL's curated content:
  - `get_for_you_page` — personalized "For You" recommendations
  - `explore_tidal` — editorial/trending content ("what's new on TIDAL?")
  - `get_tidal_moods` — list browsable moods (Chill, Party, Workout, etc.)
  - `browse_tidal_mood` — drill into a mood's curated playlists and albums
  - `get_tidal_genres` — list available music genres
  - `browse_tidal_genre` — browse genre content by type (playlists, artists, albums, tracks, videos)
- 6 new Flask endpoints: GET `/api/discover/for-you`, `/api/discover/explore`, `/api/discover/moods`, `/api/discover/moods/<api_path>`, `/api/discover/genres`, `/api/discover/genres/<path>/<type>`
- Generic page serialization: `serialize_page_categories()` handles deeply nested `Page → categories → items` structures, reusing all existing formatters via type-dispatch
- `format_page_link_data()`, `format_page_item_data()`, `format_genre_data()` formatters
- `MockPage`, `MockPageCategory`, `MockPageLink`, `MockPageItem`, `MockGenre` test classes
- 37 new tests (21 Flask + 16 MCP)

#### Phase 5: Playlist Editing (PR #11)
- **Playlist editing tools** — 5 new MCP tools for comprehensive playlist management:
  - `edit_tidal_playlist` — edit playlist title and/or description
  - `set_tidal_playlist_visibility` — make playlists public or private
  - `clear_tidal_playlist` — remove all tracks from a playlist
  - `reorder_tidal_playlist_tracks` — move tracks to different positions
  - `merge_tidal_playlists` — copy tracks from one playlist to another
- 6 new Flask endpoints for playlist operations: PATCH `/api/playlists/<id>`, POST `/api/playlists/<id>/visibility/{public|private}`, DELETE `/api/playlists/<id>/tracks/all`, POST `/api/playlists/<id>/tracks/reorder`, POST `/api/playlists/<id>/merge`
- `mcp_patch()` HTTP helper for PATCH requests
- Extended `check_user_playlist()` to validate edit, move, clear, merge, and visibility operations
- Extended `MockUserPlaylist` with 8 new methods and `public` attribute

#### Phase 3: Mixes & Radio (PR #9)
- **Mixes tools** — 2 new MCP tools for personalized TIDAL mixes:
  - `get_user_mixes` — retrieve all user's personalized mixes
  - `get_mix_tracks` — get tracks from a specific mix
- 2 new Flask endpoints: GET `/api/mixes`, GET `/api/mixes/<id>/tracks`
- `format_mix_data()` formatter for mix objects
- `MockMix` test class
- Mixes tool documentation (`docs/tools/mixes.md`)

#### Phase 2: Album & Track Details (PR #8)
- **Album & track detail tools** — 6 new MCP tools:
  - `get_album_info` — comprehensive album details with audio quality, popularity, review
  - `get_album_tracks` — paginated album track listing
  - `get_similar_albums` — discover similar albums
  - `get_album_review` — editorial album reviews
  - `get_track_info` — detailed track metadata with ISRC, audio quality
  - `get_track_lyrics` — track lyrics when available
- 6 new Flask endpoints for albums and tracks
- `format_album_detail_data()`, `format_track_detail_data()`, `format_lyrics_data()` formatters
- Extended `MockAlbum` with `tracks()`, `similar()`, `review()` methods
- Extended `MockTrack` with `lyrics()` method
- `MockLyrics` test class
- Album and track tool documentation (`docs/tools/albums.md`, `docs/tools/tracks.md`)

#### Phase 1: Artist Deep-Dive (PR #5)
- **Artist deep-dive** — 5 new Flask endpoints and 5 new MCP tools:
  - `get_artist_info` — artist details with bio and roles
  - `get_artist_top_tracks` — most popular tracks
  - `get_artist_albums` — albums with filter (albums/ep_singles/other)
  - `get_similar_artists` — discover related artists
  - `get_artist_radio` — radio mix based on artist
- `get_entity_or_404()` generic entity lookup helper
- `format_artist_detail_data()` extended artist formatter with bio and roles
- Artist tool documentation (`docs/tools/artists.md`)

#### Documentation & Patterns (PR #10)
- Comprehensive implementation patterns documentation (`docs/patterns.md`) with 863 lines of real code examples
- Pattern coverage: formatters, Flask endpoints, MCP tools, testing, error handling, tidalapi gotchas
- Updated `CLAUDE.md` to reference patterns.md for implementation guidance

### Fixed
- `format_artist_data` now uses `artist.image(320)` instead of `artist.picture(640)` (picture is a string UUID attribute, not a callable method; 640 is not a valid image dimension)
- Role enum serialization — `artist.roles` values are now serialized to strings for JSON responses

### Added (Phase 0)
- Ruff linter/formatter configuration in `pyproject.toml`
- GitHub Actions CI workflow (lint, format check, tests on Python 3.10-3.12)
- CHANGELOG.md for tracking changes
- `CLAUDE.md` with project coding standards and conventions
- `docs/` directory with detailed tool documentation, setup guide, workflows, troubleshooting, and development guide
- Health check endpoint (`GET /health`)
- Shared `requests.Session` with connection pooling and 30s default timeout
- `mcp_get`/`mcp_post`/`mcp_delete` helper functions for MCP tools
- Shared mock classes in `tests/conftest.py`

### Changed
- Updated `.gitignore` with comprehensive Python project entries
- Extracted Flask endpoints into Blueprint route modules (`tidal_api/routes/`)
- Converted Flask app to factory pattern (`create_app()`)
- Extracted MCP tools into modular subpackage (`mcp_server/tools/`)
- Replaced all `print()` calls with `logging` module
- Replaced bare `except Exception` with specific exception types (`requests.RequestException`, `requests.JSONDecodeError`)
- Fixed subprocess stdout deadlock (use `DEVNULL` instead of `PIPE`)
- Fixed silent exception swallowing in `remove_tracks_from_playlist` (now logs failures and returns `failed_track_ids`)
- Simplified `safe_attr()` — removed redundant `hasattr` guard
- Restructured tests into nested modules (`tests/tidal_api/`, `tests/mcp_server/`)
- Slimmed down README, moved detailed content to `docs/`

## [0.1.0] - 2024-01-01

### Added
- Initial release with 10 MCP tools
- Flask backend with 12 API endpoints
- TIDAL authentication via browser OAuth flow
- Search across artists, tracks, albums, playlists, and videos
- Favorite tracks retrieval with pagination
- Track recommendations (single and batch with concurrency)
- Playlist CRUD: create, list, get tracks, delete
- Add/remove tracks from playlists
- Pagination support for large collections (up to 5000 items)
