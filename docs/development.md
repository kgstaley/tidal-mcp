# Development

## Project Structure

```
tidal-mcp/
├── mcp_server/
│   ├── server.py              # FastMCP init + tool module imports
│   ├── utils.py               # Shared HTTP helpers, validation, Flask lifecycle
│   └── tools/
│       ├── __init__.py
│       ├── auth.py            # tidal_login tool
│       ├── tracks.py          # get_favorite_tracks, recommend_tracks
│       ├── playlists.py       # Playlist CRUD tools
│       └── search.py          # search_tidal tool
├── tidal_api/
│   ├── app.py                 # Flask app factory + blueprint registration
│   ├── browser_session.py     # Browser-based OAuth session management
│   ├── utils.py               # Formatters, helpers, constants
│   └── routes/
│       ├── __init__.py
│       ├── auth.py            # /api/auth/* endpoints
│       ├── tracks.py          # /api/tracks, /api/recommendations/*
│       ├── playlists.py       # /api/playlists/* endpoints
│       └── search.py          # /api/search endpoint
├── tests/
│   ├── conftest.py            # Shared mock classes
│   ├── tidal_api/
│   │   ├── conftest.py        # Flask test client fixtures
│   │   ├── test_playlists.py
│   │   ├── test_search.py
│   │   └── test_utils.py
│   └── mcp_server/
│       ├── conftest.py        # MCP module setup + auth fixtures
│       ├── test_playlists.py
│       ├── test_search.py
│       └── test_utils.py
├── docs/                      # Documentation
├── pyproject.toml             # Dependencies + tool configuration
└── README.md
```

## Running Tests

```bash
# Full suite
uv run python3 -m pytest

# Verbose output
uv run python3 -m pytest -v

# Single file
uv run python3 -m pytest tests/tidal_api/test_playlists.py

# Single test layer
uv run python3 -m pytest tests/mcp_server/
```

## Linting & Formatting

```bash
# Check for lint errors
uv run ruff check .

# Auto-fix lint errors
uv run ruff check . --fix

# Check formatting
uv run ruff format --check .

# Apply formatting
uv run ruff format .
```

## Architecture

For detailed implementation patterns and code examples, see [patterns.md](patterns.md).

TIDAL MCP uses a two-tier architecture:

```
┌─────────────────┐     stdio      ┌─────────────────┐     HTTP      ┌─────────────────┐
│  Claude Desktop │ ◄────────────► │   MCP Server    │ ◄───────────► │  Flask Backend  │
│   (MCP Client)  │                │   (server.py)   │               │   (TIDAL API)   │
└─────────────────┘                └─────────────────┘               └─────────────────┘
```

1. **MCP Server**: Communicates with Claude Desktop via the Model Context Protocol, exposing tools that Claude can use
2. **Flask Backend**: Handles all TIDAL API interactions (authentication, searching, playlist management)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure `uv run python3 -m pytest` passes
5. Ensure `uv run ruff check . && uv run ruff format --check .` passes
6. Submit a pull request
