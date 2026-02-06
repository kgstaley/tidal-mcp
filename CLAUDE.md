# CLAUDE.md

## Project Overview

TIDAL MCP — an MCP server bridging Claude with the TIDAL music streaming API.

## Architecture

- `tidal_api/routes/` — Flask Blueprints (one per domain)
- `mcp_server/tools/` — MCP tool modules (one per domain)
- `tidal_api/utils.py` — Shared formatters, helpers, constants
- `mcp_server/utils.py` — MCP-side validation, HTTP helpers, error handling
- `tests/` — Nested test modules mirroring source layout

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

- Every new feature must include tests (Flask endpoints + MCP tools + formatters)
- Tests in `tests/tidal_api/` for Flask, `tests/mcp_server/` for MCP
- Shared mock classes in `tests/conftest.py`
- All tests must pass before merging: `uv run python3 -m pytest`
- **When tests fail due to unexpected API responses or method signatures**, verify against the actual tidalapi library source and TIDAL API docs before assuming test/code is correct. Check the installed package at `.venv/lib/python3.10/site-packages/tidalapi/` for exact method signatures, parameter names, and return types. Do not guess — read the source.

## Git Conventions

- Each feature on its own branch, branched from `main`
- Small, focused commits (one logical change per commit)
- PRs go to user's fork (`kgstaley/tidal-mcp`), not upstream (`yuhuacheng/tidal-mcp`), unless explicitly told otherwise
- Draft PRs via `gh pr create --draft --repo kgstaley/tidal-mcp`
- No "Co-Authored-By" lines in commit messages

## Patterns

- Flask endpoints: use `get_entity_or_404(session, "artist", id)` for lookups, `format_*_data()` for responses
- MCP tools: use `mcp_get/mcp_post/mcp_delete()` helpers (auth check + timeout + error handling)
- Detail formatters extend base formatters via dict spread: `{**format_artist_data(artist), "bio": val}`

## tidalapi Reference (v0.8.3)

Key gotchas discovered from the installed library source:
- `artist.image(dim)` is the method (returns URL), `artist.picture` is a string UUID attribute. Valid dims: 160, 320, 480, 750
- `album.image(dim)` same pattern. Valid dims: 80, 160, 320, 640, 1280
- `artist.get_radio()` and `artist.get_similar()` take NO arguments (limit hardcoded)
- `artist.get_top_tracks(limit=None, offset=0)` — `None` limit falls back to session default (1000)
- `artist.roles` is `Optional[List[Role]]` where `Role` is an Enum — must serialize `.value` for JSON
- `session.search()` returns a `TypedDict` (dict), not an object — use `results.get('key', [])` not `results.key`
- `fetch_all_paginated` calls `fetch_fn(limit=..., offset=...)` with keyword args — pass tidalapi methods directly (no lambda wrapper needed)
- Always check `.venv/lib/python3.10/site-packages/tidalapi/` for ground truth on method signatures
