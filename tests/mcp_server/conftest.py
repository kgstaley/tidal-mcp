"""MCP server-specific fixtures and module setup."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.conftest import MockResponse

# Add project paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))

# Import the real utils module first to get the actual helper functions
spec = importlib.util.spec_from_file_location(
    "mcp_utils_real", Path(__file__).parent.parent.parent / "mcp_server" / "utils.py"
)
mcp_utils_real = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_utils_real)

# Mock the utils module before importing server, but use real helper functions
mock_utils = MagicMock()
mock_utils.start_flask_app = MagicMock()
mock_utils.shutdown_flask_app = MagicMock()
mock_utils.FLASK_APP_URL = "http://localhost:5050"
mock_utils.FLASK_PORT = 5050
mock_utils.DEFAULT_TIMEOUT = 30
# Use real implementations for helper functions
mock_utils.error_response = mcp_utils_real.error_response
mock_utils.check_tidal_auth = mcp_utils_real.check_tidal_auth
mock_utils.handle_api_response = mcp_utils_real.handle_api_response
mock_utils.validate_list = mcp_utils_real.validate_list
mock_utils.validate_string = mcp_utils_real.validate_string
mock_utils.mcp_get = mcp_utils_real.mcp_get
mock_utils.mcp_post = mcp_utils_real.mcp_post
mock_utils.mcp_delete = mcp_utils_real.mcp_delete
mock_utils.http = mcp_utils_real.http
sys.modules["utils"] = mock_utils


@pytest.fixture
def mock_auth_success(mocker):
    """Mock successful authentication check."""

    def auth_side_effect(url, **kwargs):
        if "/api/auth/status" in url:
            return MockResponse({"authenticated": True})
        return MockResponse({}, 404)

    return mocker.patch.object(mcp_utils_real.http, "get", side_effect=auth_side_effect)


@pytest.fixture
def mock_auth_failure(mocker):
    """Mock failed authentication check."""

    def auth_side_effect(url, **kwargs):
        if "/api/auth/status" in url:
            return MockResponse({"authenticated": False})
        return MockResponse({}, 404)

    return mocker.patch.object(mcp_utils_real.http, "get", side_effect=auth_side_effect)
