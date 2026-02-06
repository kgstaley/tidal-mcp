# Development

## Project Structure

```
tidal-mcp/
├── mcp_server/
│   ├── mcp_app.py             # FastMCP instance (shared singleton)
│   ├── server.py              # MCP init, Flask lifecycle, tool module imports
│   ├── utils.py               # Shared HTTP helpers, validation, Flask lifecycle
│   └── tools/
│       ├── __init__.py
│       ├── albums.py          # Album/track detail tools
│       ├── artists.py         # Artist deep-dive tools
│       ├── auth.py            # tidal_login tool
│       ├── discovery.py       # Discovery & browsing tools
│       ├── favorites.py       # Favorites CRUD tools
│       ├── mixes.py           # Mixes tools
│       ├── playlists.py       # Playlist CRUD tools
│       ├── search.py          # search_tidal tool
│       └── tracks.py          # get_favorite_tracks, recommend_tracks
├── tidal_api/
│   ├── app.py                 # Flask app factory + blueprint registration
│   ├── browser_session.py     # Browser-based OAuth session management
│   ├── utils.py               # Formatters, helpers, constants
│   └── routes/
│       ├── __init__.py
│       ├── albums.py          # /api/albums/* endpoints
│       ├── artists.py         # /api/artists/* endpoints
│       ├── auth.py            # /api/auth/* endpoints
│       ├── discovery.py       # /api/discover/* endpoints
│       ├── favorites.py       # /api/favorites/* endpoints
│       ├── mixes.py           # /api/mixes/* endpoints
│       ├── playlists.py       # /api/playlists/* endpoints
│       ├── search.py          # /api/search endpoint
│       └── tracks.py          # /api/tracks, /api/recommendations/*
├── tests/
│   ├── conftest.py            # Shared mock classes
│   ├── tidal_api/
│   │   ├── conftest.py        # Flask test client fixtures
│   │   └── test_*.py          # Flask endpoint tests
│   └── mcp_server/
│       ├── conftest.py        # MCP module setup + auth fixtures
│       └── test_*.py          # MCP tool tests
├── docs/                      # Documentation
├── .env.example               # Environment variable template
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
