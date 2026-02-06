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
