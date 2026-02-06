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

2. Create a virtual environment and install dependencies using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package with all dependencies:
   ```bash
   uv pip install --editable .
   ```

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

By default, the server uses `tidalapi`'s built-in OAuth client credentials with a device code flow. These are hardcoded in the library and may stop working if TIDAL revokes them. To avoid this, you can supply your own credentials via environment variables.

When custom credentials are set, authentication switches to the **PKCE flow**: the browser opens directly to TIDAL's login page, and after you sign in, TIDAL redirects back to a local callback endpoint that captures the tokens automatically. No manual code entry is needed.

> **Note:** Personal TIDAL developer app credentials do not support the device code flow — you **must** use custom credentials with PKCE if you registered your own app in the [TIDAL Developer Portal](https://developer.tidal.com/).

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
| `TIDAL_REDIRECT_URI` | PKCE redirect URI (default: `http://localhost:{port}/api/auth/callback`) | No |

If `TIDAL_CLIENT_ID` / `TIDAL_CLIENT_SECRET` are not set, the server falls back to `tidalapi`'s defaults with the device code flow.

**Setting up your TIDAL Developer App for PKCE:**

1. Register an app at [developer.tidal.com](https://developer.tidal.com/)
2. Set the redirect URI to `http://localhost:{your_port}/api/auth/callback` (e.g., `http://localhost:5100/api/auth/callback`)
3. Copy the Client ID and Client Secret into your MCP config
4. If using a non-default redirect URI, also set `TIDAL_REDIRECT_URI` to match exactly what you registered

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

**How it works behind the scenes:**

- **With custom credentials (PKCE flow):** The browser opens TIDAL's login page. After you sign in, TIDAL redirects to `localhost` where the server captures the authorization code and exchanges it for tokens. You'll see a "Login successful!" page in your browser.
- **Without custom credentials (device code flow):** The browser opens a TIDAL page with a pre-filled device code. After you confirm, the server detects the authorization and saves the session.
