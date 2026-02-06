"""FastMCP application instance.

Extracted to its own module to prevent double-loading when `mcp run`
imports server.py under a synthetic module name. Both server.py and
all tool modules import `mcp` from here, guaranteeing a single instance.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TIDAL MCP")
