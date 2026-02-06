"""TIDAL MCP Server — FastMCP initialization and tool registration."""

import atexit
import logging
import sys

from mcp_app import mcp  # noqa: F401 — re-exported for `mcp run` discovery
from utils import (
    FLASK_PORT,
    shutdown_flask_app,
    start_flask_app,
)

# Ensure all logging goes to stderr (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

logger.info("TIDAL MCP starting on port %s", FLASK_PORT)

# Start the Flask app when this script is loaded
logger.info("MCP server module is being loaded. Starting Flask app...")
start_flask_app()

# Register the shutdown function to be called when the MCP server exits
atexit.register(shutdown_flask_app)

# Import tool modules to register them with the mcp instance
import tools.albums  # noqa: E402, F401
import tools.artists  # noqa: E402, F401
import tools.auth  # noqa: E402, F401
import tools.discovery  # noqa: E402, F401
import tools.favorites  # noqa: E402, F401
import tools.mixes  # noqa: E402, F401
import tools.playlists  # noqa: E402, F401
import tools.search  # noqa: E402, F401
import tools.tracks  # noqa: E402, F401
