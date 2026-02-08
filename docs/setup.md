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

A template is provided at `.env.example` showing all supported environment variables. Copy it to `.env` for local development:

```bash
cp .env.example .env
# Edit .env with your credentials
```

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

## Troubleshooting Authentication

### 415 Unsupported Media Type Error

If you encounter authentication failures with error messages about "415" or "Content-Type not supported", this is a known issue with tidalapi v0.8.11.

**The fix is automated:** The project includes a patch that's automatically applied during installation. To verify it's working:

```bash
# Quick verification test
uv run python3 << 'EOF'
import base64, requests
client_id = base64.b64decode(base64.b64decode(b"WmxneVNuaGtiVzUw") + base64.b64decode(b"V2xkTE1HbDRWQT09")).decode("utf-8")
r = requests.post("https://auth.tidal.com/v1/oauth2/device_authorization", data={"client_id": client_id, "scope": "r_usr w_usr w_sub"}, timeout=10)
print(f"Status: {r.status_code} - {'✓ Working' if r.ok else '✗ Broken'}")
EOF
```

**Expected output:** `Status: 200 - ✓ Working`

If the patch isn't working:
1. Manually reapply: `bash scripts/apply-patches.sh`
2. See [docs/tidalapi-patch.md](tidalapi-patch.md) for manual patch instructions

**Technical details:** See [docs/tidalapi-patch.md](tidalapi-patch.md) for the full explanation of the bug and fix
