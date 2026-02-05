# TIDAL MCP: My Custom Picks 🌟🎧

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

- 🌟 **Music Recommendations**: Get personalized track recommendations based on your listening history **plus your custom criteria**.
- ၊၊||၊ **Playlist Management**: Create, view, and manage your TIDAL playlists
- 🔍 **Catalog Search**: Search TIDAL for artists, tracks, albums, playlists, and videos
- 📚 **Large Collection Support**: Fetch up to 5000 tracks with automatic pagination (handles TIDAL's 50-item-per-request limit)

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- TIDAL subscription

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yuhuacheng/tidal-mcp.git
   cd tidal-mcp
   ```

2. Create a virtual environment and install dependencies using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package with all dependencies from the pyproject.toml file:
   ```bash
   uv pip install --editable .
   ```

   This will install all dependencies defined in the pyproject.toml file and set up the project in development mode.


## MCP Client Configuration

### Claude Desktop Configuration

To add this MCP server to Claude Desktop, you need to update the MCP configuration file. Here's an example configuration:
(you can specify the port by adding an optional `env` section with the `TIDAL_MCP_PORT` environment variable)

```json
{
  "mcpServers": {
    "TIDAL Integration": {
      "command": "/path/to/your/uv",
      "env": {
        "TIDAL_MCP_PORT": "5100"
      },
      "args": [
        "run",
        "--with",
        "requests",
        "--with",
        "mcp[cli]",
        "--with",
        "flask",
        "--with",
        "tidalapi",
        "mcp",
        "run",
        "/path/to/your/project/tidal-mcp/mcp_server/server.py"
      ]
    }
  }
}
```

Example screenshot of the MCP configuration in Claude Desktop:
![Claude MCP Configuration](./assets/claude_desktop_config.png)

### Steps to Install MCP Configuration

1. Open Claude Desktop
2. Go to Settings > Developer
3. Click on "Edit Config"
4. Paste the modified JSON configuration
5. Save the configuration
6. Restart Claude Desktop

## How It Works

TIDAL MCP uses a two-tier architecture:

```
┌─────────────────┐     stdio      ┌─────────────────┐     HTTP      ┌─────────────────┐
│  Claude Desktop │ ◄────────────► │   MCP Server    │ ◄───────────► │  Flask Backend  │
│   (MCP Client)  │                │   (server.py)   │               │   (TIDAL API)   │
└─────────────────┘                └─────────────────┘               └─────────────────┘
```

1. **MCP Server**: Communicates with Claude Desktop via the Model Context Protocol, exposing tools that Claude can use
2. **Flask Backend**: Handles all TIDAL API interactions (authentication, searching, playlist management)

**Privacy**: Your TIDAL credentials and session data stay local on your machine. Authentication happens directly between your browser and TIDAL.

## Usage Guide

### First-Time Setup

1. **Start a conversation** with Claude Desktop after configuring the MCP server
2. **Ask Claude to log in to TIDAL**: *"Please log me in to TIDAL"*
3. **Authenticate**: Your browser will open to TIDAL's login page. Sign in with your TIDAL account.
4. **Session persists**: Once authenticated, your session is saved locally. You won't need to log in again unless the session expires.

### Common Workflows

**Getting Personalized Recommendations**
```
You: "Based on my recent favorites, recommend some similar tracks but more upbeat and from the last 2 years"
Claude: [Uses get_favorite_tracks → recommend_tracks → presents curated list]
```

**Searching and Adding to Playlists**
```
You: "Search for songs by Khruangbin and add the top 5 to my 'Chill Vibes' playlist"
Claude: [Uses search_tidal → get_user_playlists → add_tracks_to_playlist]
```

**Creating a Themed Playlist**
```
You: "Create a playlist called 'Late Night Jazz' with recommendations based on my playlist 'Evening Relaxation'"
Claude: [Uses get_playlist_tracks → recommend_tracks → create_tidal_playlist]
```

**Cleaning Up Playlists**
```
You: "Show me my playlist 'Road Trip Mix' and remove any duplicate tracks"
Claude: [Uses get_playlist_tracks → remove_tracks_from_playlist]
```

## Available Tools

### Authentication

| Tool | Description |
|------|-------------|
| `tidal_login` | Authenticate with TIDAL through browser login flow |

### Library Access

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_favorite_tracks` | `limit` (default: 50, max: 5000) | Retrieve your favorite/saved tracks |
| `search_tidal` | `query`, `types` (optional), `limit` (default: 20) | Search TIDAL catalog for artists, tracks, albums, playlists, videos |
| `recommend_tracks` | `track_ids` (optional), `filter_criteria` (optional), `limit_per_track`, `limit_from_favorite` | Get personalized recommendations based on specific tracks or your favorites |

### Playlist Management

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_user_playlists` | — | List all your TIDAL playlists |
| `get_playlist_tracks` | `playlist_id`, `limit` (default: 50, max: 5000) | Get all tracks from a specific playlist |
| `create_tidal_playlist` | `title`, `track_ids`, `description` (optional) | Create a new playlist with specified tracks |
| `add_tracks_to_playlist` | `playlist_id`, `track_ids`, `allow_duplicates` (default: false), `position` (default: end) | Add tracks to an existing playlist |
| `remove_tracks_from_playlist` | `playlist_id`, `track_ids` | Remove tracks from a playlist |
| `delete_tidal_playlist` | `playlist_id` | Delete a playlist from your account |

## Suggested Prompt Starters

Once configured, you can interact with your TIDAL account through Claude by asking questions like:

**Recommendations**
- *"Recommend songs like those in this playlist, but slower and more acoustic."*
- *"Create a playlist based on my top tracks, but focused on chill, late-night vibes."*
- *"Find songs like these in playlist XYZ but in languages other than English."*

**Search & Discovery**
- *"Search for albums by Radiohead and show me their most recent releases."*
- *"Find tracks similar to 'Bohemian Rhapsody' and add them to a new playlist."*

**Playlist Management**
- *"Add the top 10 results from searching 'lo-fi beats' to my study playlist."*
- *"Remove any tracks by artist X from my workout playlist."*
- *"Show me all my playlists and how many tracks each has."*

*💡 You can also ask the model to:*
- Use more tracks as seeds to broaden the inspiration.
- Return more recommendations if you want a longer playlist.
- Or delete a playlist if you're not into it — no pressure!

## Troubleshooting

### Authentication Issues

**Browser doesn't open for login**
- Ensure your default browser is set correctly in your system settings
- Try manually opening the URL that Claude provides in the response

**Session expired**
- Simply ask Claude to log in again: *"Please log me in to TIDAL"*
- Sessions typically last several days before requiring re-authentication

### Connection Issues

**"Failed to connect to TIDAL service" errors**
- Verify the Flask backend is running (check for port conflicts)
- Try changing the port via `TIDAL_MCP_PORT` environment variable
- Restart Claude Desktop to reload the MCP server

**Port conflicts**
- Default port is 5001. If occupied, set a custom port in your MCP config:
  ```json
  "env": { "TIDAL_MCP_PORT": "5100" }
  ```

### Common Questions

**Where are my credentials stored?**
- Your TIDAL session is stored locally in `~/.config/tidal-mcp/` (Linux/macOS) or equivalent on Windows
- No credentials are sent to Claude or any external service

**Do I need a TIDAL subscription?**
- Yes, a TIDAL subscription is required to access the API features

**Why do some tracks not have recommendations?**
- Not all tracks in TIDAL's catalog have recommendation data available
- Try using different seed tracks if recommendations are sparse

## Development

### Running Tests

```bash
uv run python3 -m pytest
```

To run with verbose output:
```bash
uv run python3 -m pytest -v
```

### Project Structure

```
tidal-mcp/
├── mcp_server/
│   ├── server.py      # MCP server with tool definitions
│   └── utils.py       # Flask backend management utilities
├── tidal_api/
│   └── app.py         # Flask app with TIDAL API routes
├── tests/             # Test suite
├── pyproject.toml     # Project dependencies
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

[MIT License](LICENSE)

## Acknowledgements

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- [TIDAL Python API](https://github.com/tamland/python-tidal)
