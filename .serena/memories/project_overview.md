# Project Overview

## Purpose
MCP server bridging Claude with the TIDAL music streaming API. Enables Claude to interact with TIDAL's catalog, playlists, favorites, and discovery features through natural language.

## Tech Stack
- **Python 3.10+** - Core language
- **Flask** - Web backend (port 5050)
- **MCP (Model Context Protocol)** - stdio interface for Claude integration
- **tidal_client** - Custom TIDAL API client (replacing tidalapi v0.8.3)
- **requests** - HTTP client for TIDAL API and internal communication
- **pytest + pytest-mock** - Testing framework

## Runtime Architecture
- **MCP server** (`mcp_server/server.py`) auto-starts Flask backend as subprocess on port 5050
- **Flask process** cleaned up via `atexit` handler
- **MCP tools** call Flask endpoints over HTTP using shared `requests.Session`
- **Port override**: Set `TIDAL_MCP_PORT` environment variable

## Authentication Flow
1. OAuth device flow via `tidal_client/auth.py` (start_device_auth, poll_for_token)
2. Session tokens saved to `tempfile.gettempdir()/tidal-session-oauth.json`
3. Session reloaded per-request via `@requires_tidal_auth` decorator
4. Tokens refreshed automatically by `tidal_client.session.TidalSession`

## Key Features
- **Music Recommendations**: Get personalized track/artist recommendations
- **Favorites Management**: Add/remove tracks, albums, artists, videos
- **Playlist CRUD**: Create, update, delete, reorder user playlists
- **Catalog Search**: Search tracks, albums, artists, playlists, videos
- **Discovery**: Explore mixes, artist radio, similar artists, top tracks

## Project Structure
- `tidal_client/` - Custom TIDAL API client (OAuth, session, HTTP)
  - `config.py` - API URLs and configuration
  - `session.py` - TidalSession class (OAuth, HTTP requests, token management)
  - `auth.py` - OAuth device flow functions
  - `exceptions.py` - Custom exception hierarchy
  - `models/` - TypedDict models for API responses
  - `endpoints/` - API endpoint functions
- `tidal_api/routes/` - Flask blueprints (one per domain)
- `mcp_server/tools/` - MCP tool modules (matching route structure)
- `tidal_api/utils.py` - Shared formatters and helpers
- `mcp_server/utils.py` - MCP validation and HTTP helpers
- `tests/` - Nested test modules mirroring source layout
  - `tests/tidal_client/` - Tests for custom TIDAL client
