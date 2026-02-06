"""Tests for tidal_login MCP tool."""

from unittest.mock import patch

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestTidalLogin:
    """Tests for tidal_login MCP tool."""

    def test_login_immediate_success(self, mocker):
        """Test login returns success when already authenticated."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"status": "success", "message": "Authenticated", "user_id": 123}),
        )

        from tools.auth import tidal_login

        result = tidal_login()
        assert result["status"] == "success"

    def test_login_device_code_error(self, mocker):
        """Test login returns error on non-200 response."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"message": "Auth failed"}, 401),
        )

        from tools.auth import tidal_login

        result = tidal_login()
        assert result["status"] == "error"
        assert "failed" in result["message"].lower()

    def test_login_pkce_polls_until_success(self, mocker):
        """Test that PKCE pending triggers polling and returns when auth completes."""
        call_count = 0

        def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "/api/auth/login" in url:
                return MockResponse({"status": "pending", "flow": "pkce"})
            if "/api/auth/status" in url:
                # First two polls: not yet authenticated. Third: success.
                if call_count <= 3:
                    return MockResponse({"authenticated": False})
                return MockResponse(
                    {
                        "authenticated": True,
                        "user": {"id": 456, "username": "tidal_user", "email": "user@example.com"},
                    }
                )
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.auth import tidal_login

        with patch("tools.auth.time.sleep"):
            result = tidal_login()

        assert result["status"] == "success"
        assert result["user"]["id"] == 456

    def test_login_pkce_timeout(self, mocker):
        """Test that PKCE polling times out when auth never completes."""

        def mock_get(url, **kwargs):
            if "/api/auth/login" in url:
                return MockResponse({"status": "pending", "flow": "pkce"})
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": False})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.auth import tidal_login

        with patch("tools.auth.time.sleep"), patch("tools.auth.time.monotonic", side_effect=[0, 0, 200]):
            result = tidal_login()

        assert result["status"] == "error"
        assert "timed out" in result["message"].lower()

    def test_login_connection_error(self, mocker):
        """Test login handles connection failure gracefully."""
        import requests

        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            side_effect=requests.ConnectionError("Connection refused"),
        )

        from tools.auth import tidal_login

        result = tidal_login()
        assert result["status"] == "error"
        assert "connect" in result["message"].lower()
