"""TIDAL MCP Server — FastMCP initialization and tool registration."""

import atexit
import logging
import signal
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

# Ensure Flask is cleaned up on normal exit AND on SIGTERM/SIGINT.
# atexit only fires on normal interpreter exit — not when the process
# is killed via signal, which is how Claude Desktop stops MCP servers.
atexit.register(shutdown_flask_app)


def _handle_shutdown_signal(signum: int, _frame) -> None:
    sig_name = signal.Signals(signum).name
    logger.info("Received %s, shutting down Flask subprocess...", sig_name)
    shutdown_flask_app()
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_shutdown_signal)
signal.signal(signal.SIGINT, _handle_shutdown_signal)

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
