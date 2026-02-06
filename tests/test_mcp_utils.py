"""Unit tests for mcp_server/utils.py helper functions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project paths for imports
mcp_server_path = str(Path(__file__).parent.parent / "mcp_server")
if mcp_server_path not in sys.path:
    sys.path.insert(0, mcp_server_path)

# Import directly from the file to avoid module caching issues
import importlib.util

spec = importlib.util.spec_from_file_location("mcp_utils", Path(__file__).parent.parent / "mcp_server" / "utils.py")
mcp_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_utils)

error_response = mcp_utils.error_response
check_tidal_auth = mcp_utils.check_tidal_auth
handle_api_response = mcp_utils.handle_api_response
validate_list = mcp_utils.validate_list
validate_string = mcp_utils.validate_string


class TestErrorResponse:
    """Tests for error_response function."""

    def test_basic_error_response(self):
        result = error_response("Something went wrong")

        assert result["status"] == "error"
        assert result["message"] == "Something went wrong"

    def test_empty_message(self):
        result = error_response("")

        assert result["status"] == "error"
        assert result["message"] == ""

    def test_long_message(self):
        long_msg = "x" * 1000
        result = error_response(long_msg)

        assert result["status"] == "error"
        assert result["message"] == long_msg


class TestCheckTidalAuth:
    """Tests for check_tidal_auth function."""

    def test_authenticated_returns_none(self):
        """When authenticated, should return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"authenticated": True}

        with patch.object(mcp_utils.requests, "get", return_value=mock_response):
            result = check_tidal_auth("test action")

        assert result is None

    def test_not_authenticated_returns_error(self):
        """When not authenticated, should return error dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"authenticated": False}

        with patch.object(mcp_utils.requests, "get", return_value=mock_response):
            result = check_tidal_auth("test action")

        assert result is not None
        assert result["status"] == "error"
        assert "login" in result["message"].lower()
        assert "test action" in result["message"]

    def test_custom_action_in_message(self):
        """The action should appear in the error message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"authenticated": False}

        with patch.object(mcp_utils.requests, "get", return_value=mock_response):
            result = check_tidal_auth("create a playlist")

        assert "create a playlist" in result["message"]

    def test_default_action(self):
        """Should use default action if not provided."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"authenticated": False}

        with patch.object(mcp_utils.requests, "get", return_value=mock_response):
            result = check_tidal_auth()

        assert "perform this action" in result["message"]

    def test_exception_returns_error(self):
        """When an exception occurs, should return error dict."""
        with patch.object(mcp_utils.requests, "get", side_effect=Exception("Network error")):
            result = check_tidal_auth("test action")

        assert result is not None
        assert result["status"] == "error"
        assert "Network error" in result["message"]


class TestHandleApiResponse:
    """Tests for handle_api_response function."""

    def test_200_returns_none(self):
        """HTTP 200 should return None (success)."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        result = handle_api_response(mock_response, "playlist")

        assert result is None

    def test_401_returns_auth_error(self):
        """HTTP 401 should return authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        result = handle_api_response(mock_response, "playlist")

        assert result is not None
        assert result["status"] == "error"
        assert "authenticated" in result["message"].lower()

    def test_404_returns_not_found_error(self):
        """HTTP 404 should return not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        result = handle_api_response(mock_response, "playlist")

        assert result is not None
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_404_with_resource_id(self):
        """HTTP 404 should include resource ID in message."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        result = handle_api_response(mock_response, "playlist", "abc-123")

        assert result is not None
        assert "abc-123" in result["message"]

    def test_403_returns_forbidden_error(self):
        """HTTP 403 should return forbidden error."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        result = handle_api_response(mock_response, "playlist")

        assert result is not None
        assert result["status"] == "error"
        assert "cannot modify" in result["message"].lower()

    def test_500_returns_generic_error(self):
        """HTTP 500 should return generic error with details."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        result = handle_api_response(mock_response, "playlist")

        assert result is not None
        assert result["status"] == "error"
        assert "Internal server error" in result["message"]

    def test_generic_error_with_json_parse_failure(self):
        """When JSON parsing fails, should return unknown error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Invalid JSON")

        result = handle_api_response(mock_response, "playlist")

        assert result is not None
        assert result["status"] == "error"
        assert "Unknown error" in result["message"]


class TestValidateList:
    """Tests for validate_list function."""

    def test_valid_list_returns_none(self):
        """Valid non-empty list should return None."""
        result = validate_list(["item1", "item2"], "track_ids", "track ID")

        assert result is None

    def test_empty_list_returns_error(self):
        """Empty list should return error."""
        result = validate_list([], "track_ids", "track ID")

        assert result is not None
        assert result["status"] == "error"
        assert "track ID" in result["message"]

    def test_none_returns_error(self):
        """None value should return error."""
        result = validate_list(None, "track_ids", "track ID")

        assert result is not None
        assert result["status"] == "error"

    def test_non_list_returns_error(self):
        """Non-list value should return error."""
        result = validate_list("not a list", "track_ids", "track ID")

        assert result is not None
        assert result["status"] == "error"

    def test_single_item_list_is_valid(self):
        """Single item list should be valid."""
        result = validate_list(["single"], "track_ids", "track ID")

        assert result is None


class TestValidateString:
    """Tests for validate_string function."""

    def test_valid_string_returns_none(self):
        """Valid non-empty string should return None."""
        result = validate_string("valid string", "title")

        assert result is None

    def test_empty_string_returns_error(self):
        """Empty string should return error."""
        result = validate_string("", "title")

        assert result is not None
        assert result["status"] == "error"
        assert "title" in result["message"]

    def test_whitespace_only_returns_error(self):
        """Whitespace-only string should return error."""
        result = validate_string("   ", "title")

        assert result is not None
        assert result["status"] == "error"

    def test_none_returns_error(self):
        """None value should return error."""
        result = validate_string(None, "title")

        assert result is not None
        assert result["status"] == "error"

    def test_zero_returns_error(self):
        """Zero/falsy value should return error."""
        result = validate_string(0, "title")

        assert result is not None
        assert result["status"] == "error"

    def test_string_with_spaces_is_valid(self):
        """String with leading/trailing spaces is valid if non-empty."""
        result = validate_string("  valid  ", "title")

        assert result is None
