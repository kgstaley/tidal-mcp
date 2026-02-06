# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Ruff linter/formatter configuration in `pyproject.toml`
- GitHub Actions CI workflow (lint, format check, tests on Python 3.10-3.12)
- CHANGELOG.md for tracking changes

### Changed
- Updated `.gitignore` with comprehensive Python project entries

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
