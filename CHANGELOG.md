# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

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
