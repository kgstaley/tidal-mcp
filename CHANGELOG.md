# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
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
