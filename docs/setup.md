# Setup

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- TIDAL subscription

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yuhuacheng/tidal-mcp.git
   cd tidal-mcp
   ```

2. Bootstrap the development environment:
   ```bash
   script/bootstrap
   ```

   This checks for `uv` and Python 3.10+, then installs all dependencies. You can re-run it any time to sync deps.

   <details>
   <summary>Manual setup (if you prefer not to use the script)</summary>

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install --editable .
   ```
   </details>

## MCP Client Configuration

### Claude Desktop

Update the MCP configuration file with the following (optionally set a custom port via `TIDAL_MCP_PORT`):

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

### Custom OAuth Credentials (Optional)

By default, the server uses `tidalapi`'s built-in OAuth client credentials. These are hardcoded in the library and may stop working if TIDAL revokes them. To avoid this, you can supply your own credentials via environment variables:

```json
{
  "mcpServers": {
    "TIDAL Integration": {
      "command": "/path/to/your/uv",
      "env": {
        "TIDAL_MCP_PORT": "5100",
        "TIDAL_CLIENT_ID": "your_client_id",
        "TIDAL_CLIENT_SECRET": "your_client_secret"
      },
      "args": ["..."]
    }
  }
}
```

| Variable | Description | Required |
|----------|-------------|----------|
| `TIDAL_MCP_PORT` | Port for the Flask backend (default: `5050`) | No |
| `TIDAL_CLIENT_ID` | Custom OAuth client ID for TIDAL API | No |
| `TIDAL_CLIENT_SECRET` | Custom OAuth client secret for TIDAL API | No |

If `TIDAL_CLIENT_ID` / `TIDAL_CLIENT_SECRET` are not set, the server falls back to `tidalapi`'s defaults.

### Steps to Install

1. Open Claude Desktop
2. Go to Settings > Developer
3. Click on "Edit Config"
4. Paste the modified JSON configuration
5. Save the configuration
6. Restart Claude Desktop

## First-Time Authentication

1. Start a conversation with Claude Desktop after configuring the MCP server
2. Ask Claude to log in to TIDAL: *"Please log me in to TIDAL"*
3. Your browser will open to TIDAL's login page — sign in with your TIDAL account
4. Once authenticated, your session is saved locally and persists until it expires
