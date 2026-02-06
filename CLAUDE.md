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

## Git Conventions

- Each feature on its own branch, branched from `main`
- Small, focused commits (one logical change per commit)
- Draft PRs to `kgstaley/tidal-mcp` via `gh pr create --draft`
- No "Co-Authored-By" lines in commit messages

## Patterns

- Flask endpoints: use `get_playlist_or_404()` for lookups, `format_*_data()` for responses
- MCP tools: use `mcp_get/mcp_post/mcp_delete()` helpers (auth check + timeout + error handling)
- Detail formatters extend base formatters via dict spread: `{**format_album_data(album), "extra": val}`
