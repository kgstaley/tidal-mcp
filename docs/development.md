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
├── script/
│   ├── bootstrap              # Install deps, check Python version
│   ├── ci                     # Run full lint + test pipeline
│   ├── lint                   # Ruff check + format
│   ├── start                  # Launch MCP dev server or Flask
│   └── test                   # Run pytest with arg passthrough
├── .env.example               # Environment variable template
├── pyproject.toml             # Dependencies + tool configuration
└── README.md
```

## Development Scripts

The `script/` directory follows the [Scripts to Rule Them All](https://github.blog/open-source/git/scripts-to-rule-them-all/) pattern. All scripts are self-contained, accept `--help`, and can be run from any directory.

### `script/bootstrap` — Set up the development environment

```bash
script/bootstrap
```

Checks for `uv` and Python 3.10+, then runs `uv sync --all-extras`. Idempotent — safe to re-run at any time.

### `script/start` — Launch the server

```bash
script/start           # MCP dev server with web UI (auto-starts Flask)
script/start --flask   # Flask backend only on port 5050
```

Sources `.env` if present (picks up `TIDAL_MCP_PORT`, `TIDAL_CLIENT_ID`, etc.).

### `script/test` — Run the test suite

```bash
script/test                                        # Full suite
script/test -v                                     # Verbose
script/test tests/tidal_api/test_playlists.py      # Single file
script/test tests/mcp_server/ -k "test_search"     # Filter by name
```

All arguments are passed through to `pytest`.

### `script/lint` — Run linting and format checks

```bash
script/lint        # Check only (exits 1 on violations)
script/lint --fix  # Auto-fix lint issues and reformat
```

### `script/ci` — Run the full CI pipeline locally

```bash
script/ci
```

Runs `script/lint` then `script/test`. Mirrors the GitHub Actions workflow — use this before pushing.

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
2. `script/bootstrap` to set up your environment
3. Create a feature branch
4. Make your changes with tests
5. `script/ci` to verify lint + tests pass
6. Submit a pull request
