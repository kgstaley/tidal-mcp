# TIDAL MCP: My Custom Picks

![Demo: Music Recommendations in Action](./assets/tidal_mcp_demo.gif)

Most music platforms offer recommendations — Daily Discovery, Top Artists, New Arrivals, etc. — but even with the state-of-the-art system, they often feel too "aggregated". I wanted something more custom and context-aware.

With TIDAL MCP, you can ask for things like:
> *"Based on my last 10 favorites, find similar tracks — but only ones from recent years."*
>
> *"Find me tracks like those in this playlist, but slower and more acoustic."*

The LLM filters and curates results using your input, finds similar tracks via TIDAL's API, and builds new playlists directly in your account.

<a href="https://glama.ai/mcp/servers/@yuhuacheng/tidal-mcp">
  <img width="400" height="200" src="https://glama.ai/mcp/servers/@yuhuacheng/tidal-mcp/badge" alt="TIDAL: My Custom Picks MCP server" />
</a>

## Features

- **Music Recommendations**: Get personalized track recommendations based on your listening history **plus your custom criteria**
- **Favorites Management**: Add, remove, and browse favorites across artists, albums, tracks, videos, playlists, and mixes
- **Playlist Management**: Create, view, and manage your TIDAL playlists
- **Catalog Search**: Search TIDAL for artists, tracks, albums, playlists, and videos
- **Discovery & Browsing**: Explore personalized recommendations, trending content, moods, and genres
- **Large Collection Support**: Fetch up to 5000 tracks with automatic pagination

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- TIDAL subscription

### Installation

```bash
git clone https://github.com/yuhuacheng/tidal-mcp.git
cd tidal-mcp
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install --editable .
```

See [docs/setup.md](docs/setup.md) for MCP client configuration and first-time authentication.

## How It Works

```
┌─────────────────┐     stdio      ┌─────────────────┐     HTTP      ┌─────────────────┐
│  Claude Desktop │ ◄────────────► │   MCP Server    │ ◄───────────► │  Flask Backend  │
│   (MCP Client)  │                │   (server.py)   │               │   (TIDAL API)   │
└─────────────────┘                └─────────────────┘               └─────────────────┘
```

1. **MCP Server**: Communicates with Claude Desktop via the Model Context Protocol
2. **Flask Backend**: Handles all TIDAL API interactions (authentication, searching, playlist management)

**Privacy**: Your TIDAL credentials and session data stay local on your machine.

## Available Tools

| Tool | Description |
|------|-------------|
| [`tidal_login`](docs/tools/authentication.md) | Authenticate with TIDAL through browser login |
| [`get_favorite_tracks`](docs/tools/tracks.md#get_favorite_tracks) | Retrieve your saved tracks |
| [`recommend_tracks`](docs/tools/tracks.md#recommend_tracks) | Get personalized recommendations |
| [`search_tidal`](docs/tools/search.md) | Search TIDAL catalog |
| [`get_user_playlists`](docs/tools/playlists.md#get_user_playlists) | List your playlists |
| [`get_playlist_tracks`](docs/tools/playlists.md#get_playlist_tracks) | Get tracks from a playlist |
| [`create_tidal_playlist`](docs/tools/playlists.md#create_tidal_playlist) | Create a new playlist |
| [`add_tracks_to_playlist`](docs/tools/playlists.md#add_tracks_to_playlist) | Add tracks to a playlist |
| [`remove_tracks_from_playlist`](docs/tools/playlists.md#remove_tracks_from_playlist) | Remove tracks from a playlist |
| [`delete_tidal_playlist`](docs/tools/playlists.md#delete_tidal_playlist) | Delete a playlist |
| [`get_artist_info`](docs/tools/artists.md#get_artist_info) | Get artist details, bio, and roles |
| [`get_artist_top_tracks`](docs/tools/artists.md#get_artist_top_tracks) | Get an artist's top tracks |
| [`get_artist_albums`](docs/tools/artists.md#get_artist_albums) | Get an artist's albums/EPs/singles |
| [`get_similar_artists`](docs/tools/artists.md#get_similar_artists) | Find similar artists |
| [`get_artist_radio`](docs/tools/artists.md#get_artist_radio) | Get radio tracks based on an artist |
| `get_favorites` | Get favorites by type (artists, albums, tracks, videos, playlists, mixes) |
| `add_favorite` | Add an item to your favorites |
| `remove_favorite` | Remove an item from your favorites |
| `get_user_mixes` | Get your personalized mixes |
| `get_mix_tracks` | Get tracks from a specific mix |
| `get_for_you_page` | Get personalized "For You" recommendations |
| `explore_tidal` | Browse editorial and trending content |
| `get_tidal_moods` | List available mood categories |
| `browse_tidal_mood` | Browse a mood's curated content |
| `get_tidal_genres` | List available music genres |
| `browse_tidal_genre` | Browse a genre by content type |

See [docs/workflows.md](docs/workflows.md) for common usage patterns and prompt starters.

## Development

```bash
uv run python3 -m pytest          # Run tests
uv run ruff check .               # Lint
uv run ruff format --check .      # Check formatting
```

See [docs/development.md](docs/development.md) for project structure and contributing guidelines.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md).

## License

[MIT License](LICENSE)

## Acknowledgements

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- [TIDAL Python API](https://github.com/tamland/python-tidal)
