# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TIDAL MCP — an MCP server bridging Claude with the TIDAL music streaming API.

## Setup

- Python 3.10+ required (see `.python-version`)
- Install all dependencies: `uv sync --all-extras`

## Architecture

- `tidal_client/` — Custom TIDAL API client (replacing tidalapi)
  - `config.py` — API URLs and OAuth credentials
  - `session.py` — TidalSession class (OAuth, HTTP requests, token management)
  - `auth.py` — OAuth device flow functions (start_device_auth, poll_for_token, refresh_token)
  - `exceptions.py` — Custom exception hierarchy (TidalClientError, TidalAPIError, etc.)
  - `models/` — TypedDict models for API responses (future)
  - `endpoints/` — API endpoint functions (future)
- `tidal_api/routes/` — Flask Blueprints (one per domain)
- `mcp_server/tools/` — MCP tool modules (one per domain)
- `tidal_api/utils.py` — Shared formatters, helpers, constants
- `mcp_server/utils.py` — MCP-side validation, HTTP helpers, error handling
- `tests/` — Nested test modules mirroring source layout
  - `tests/tidal_client/` — Tests for custom TIDAL client

## Runtime Architecture

- MCP server (`mcp_server/server.py`) auto-starts the Flask backend as a subprocess on port 5050 (override with `TIDAL_MCP_PORT` env var)
- Flask process cleaned up via `atexit` handler
- MCP tools call Flask endpoints over HTTP using a shared `requests.Session`
- Auth: OAuth via browser → session saved to `tempfile.gettempdir()/tidal-session-oauth.json` → reloaded per-request

## Commands

- Run tests: `uv run python3 -m pytest`
- Run tests verbose: `uv run python3 -m pytest -v`
- Run single test file: `uv run python3 -m pytest tests/tidal_api/test_playlists.py`
- Lint: `ruff check .`
- Format: `ruff format .`
- Format check: `ruff format --check .`

## Code Standards

- **Python 3.10+**, type hints on all function signatures
- **Imports**: Absolute imports, grouped (stdlib, third-party, local), no star imports
- **Naming**: snake_case functions/variables, PascalCase classes, UPPER_SNAKE constants
- **Formatting**: ruff format (120 char line length), f-strings everywhere
- **Constants**: No magic numbers — define as module-level constants (`MAX_LIMIT`, `DEFAULT_TIMEOUT`, etc.)

## Error Handling

- Catch specific exceptions, never bare `except Exception`
- MCP tools: catch `requests.RequestException`, not bare `Exception`
- Use `logging` module (never `print()`), with `exc_info=True` for error tracebacks
- All HTTP requests require `timeout=30` parameter

## Testing

- Every new feature must include tests (Flask endpoints + MCP tools + formatters + tidal_client)
- Tests in `tests/tidal_api/` for Flask, `tests/mcp_server/` for MCP, `tests/tidal_client/` for TIDAL client
- All tests must pass before merging: `uv run python3 -m pytest`
- **When tests fail due to unexpected API responses or method signatures**, verify against TIDAL API docs before assuming test/code is correct
- Shared mock classes in `tests/conftest.py`: `MockArtist`, `MockAlbum`, `MockTrack`, `MockCreator`, `MockPlaylist`, `MockUserPlaylist`, `MockVideo`, `MockResponse`
- Flask test fixtures in `tests/tidal_api/conftest.py`: `client`, `mock_session_file`
- MCP test fixtures in `tests/mcp_server/conftest.py`: `mock_auth_success`, `mock_auth_failure` (mock HTTP, not Flask)
- TIDAL client test fixtures in `tests/tidal_client/conftest.py`: Mock OAuth responses, HTTP requests

## CI

- GitHub Actions: lint + format check + tests on Python 3.10, 3.11, 3.12

## Git Conventions

- Each feature on its own branch, branched from `main`
- Small, focused commits (one logical change per commit)
- PRs go to user's fork (`kgstaley/tidal-mcp`), not upstream (`yuhuacheng/tidal-mcp`), unless explicitly told otherwise
- Draft PRs via `gh pr create --draft --repo kgstaley/tidal-mcp`
- No "Co-Authored-By" lines in commit messages

## Patterns

See [docs/patterns.md](docs/patterns.md) for detailed implementation patterns with code examples.

Quick reference:
- Flask endpoints: `@requires_tidal_auth` + `@handle_endpoint_errors(action)` + `get_entity_or_404()`
- MCP tools: `check_tidal_auth()` → `validate_*()` → `mcp_get/post/delete()`
- Formatters: Base formatters + detail formatters extend via dict spread
- Testing: One test class per endpoint/tool with standard coverage (success, not_found, not_authenticated)

## tidal_client Reference

The custom TIDAL API client replacing tidalapi v0.8.3. See `.serena/memories/tidal_client_architecture.md` for detailed documentation.

**Key Components:**
- `TidalSession` — Main client class (OAuth, HTTP requests, token management)
- `start_device_auth()` — Start OAuth device flow (no browser required)
- `poll_for_token()` — Poll for access token until user authorizes
- `refresh_token()` — Refresh access token using refresh token
- Exception hierarchy: `TidalClientError` → `TidalAPIError`, `TidalAuthError`, `TidalTokenExpiredError`, `TidalRateLimitError`

**Usage Pattern:**
```python
from tidal_client import TidalSession, start_device_auth, poll_for_token

# OAuth flow
auth_data = start_device_auth()
print(f"Visit {auth_data['verification_uri']} and enter {auth_data['user_code']}")
tokens = poll_for_token(auth_data['device_code'])

# Create session (auto-refreshes tokens)
session = TidalSession(
    access_token=tokens["access_token"],
    refresh_token=tokens["refresh_token"],
)

# Make requests
response = session.request("GET", "/tracks/123")
track_data = response.json()
```

## tidalapi Reference (v0.8.3) - Legacy

**NOTE:** Being replaced by `tidal_client`. This section will be removed once migration is complete.

Key gotchas discovered from the installed library source:
- `artist.image(dim)` is the method (returns URL), `artist.picture` is a string UUID attribute. Valid dims: 160, 320, 480, 750
- `album.image(dim)` same pattern. Valid dims: 80, 160, 320, 640, 1280
- `artist.get_radio()` and `artist.get_similar()` take NO arguments (limit hardcoded)
- `artist.get_top_tracks(limit=None, offset=0)` — `None` limit falls back to session default (1000)
- `artist.roles` is `Optional[List[Role]]` where `Role` is an Enum — must serialize `.value` for JSON
- `session.search()` returns a `TypedDict` (dict), not an object — use `results.get('key', [])` not `results.key`
- `fetch_all_paginated` calls `fetch_fn(limit=..., offset=...)` with keyword args — pass tidalapi methods directly (no lambda wrapper needed)
- Always check `.venv/lib/python3.10/site-packages/tidalapi/` for ground truth on method signatures
