"""Tests for /api/auth Flask endpoints."""

import json
from unittest.mock import MagicMock


class TestLoginEndpoint:
    """Tests for /api/auth/login endpoint."""

    def test_login_existing_valid_session(self, client, mock_session_file, mocker):
        """Test login returns success when session file is valid."""
        mock_session = MagicMock()
        mock_session.check_login.return_value = True
        mock_session.user.id = 12345
        mock_session.uses_custom_credentials = False
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", mock_session_file)

        response = client.get("/api/auth/login")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["user_id"] == 12345

    def test_login_pkce_flow_returns_pending(self, client, mocker):
        """Test login with custom credentials returns pending and opens browser."""
        mock_session = MagicMock()
        mock_session.uses_custom_credentials = True
        mock_session.check_login.return_value = False
        mock_session.get_pkce_login_url.return_value = "https://login.tidal.com/authorize?client_id=test"
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", MagicMock(exists=MagicMock(return_value=False)))
        mock_browser = mocker.patch("tidal_api.routes.auth.webbrowser.open")

        response = client.get("/api/auth/login")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "pending"
        assert data["flow"] == "pkce"
        mock_browser.assert_called_once_with("https://login.tidal.com/authorize?client_id=test")

    def test_login_device_code_flow_success(self, client, mocker):
        """Test login with built-in credentials uses device code flow."""
        mock_session = MagicMock()
        mock_session.uses_custom_credentials = False
        mock_session.check_login.return_value = False
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.id = 99999
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", MagicMock(exists=MagicMock(return_value=False)))

        response = client.get("/api/auth/login")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["user_id"] == 99999

    def test_login_device_code_flow_failure(self, client, mocker):
        """Test login returns 401 when device code flow fails."""
        mock_session = MagicMock()
        mock_session.uses_custom_credentials = False
        mock_session.check_login.return_value = False
        mock_session.login_session_file_auto.return_value = False
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", MagicMock(exists=MagicMock(return_value=False)))

        response = client.get("/api/auth/login")
        assert response.status_code == 401


class TestCallbackEndpoint:
    """Tests for /api/auth/callback endpoint."""

    def test_callback_success(self, client, mocker, tmp_path):
        """Test successful PKCE callback exchanges code and saves session."""
        session_file = tmp_path / "tidal-session-oauth.json"
        mock_session = MagicMock()
        mock_session.complete_pkce_login.return_value = True
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", session_file)

        response = client.get("/api/auth/callback?code=test_auth_code")
        assert response.status_code == 200
        assert b"Login successful" in response.data
        assert response.content_type == "text/html"
        mock_session.complete_pkce_login.assert_called_once_with("test_auth_code")
        mock_session.save_session_to_file.assert_called_once_with(session_file)

    def test_callback_missing_code(self, client, mocker):
        """Test callback returns error when code param is missing."""
        mocker.patch("tidal_api.routes.auth._set_pkce_pending")

        response = client.get("/api/auth/callback")
        assert response.status_code == 400
        assert b"Login failed" in response.data

    def test_callback_with_error_param(self, client, mocker):
        """Test callback handles TIDAL error redirect (e.g., user denied access)."""
        mocker.patch("tidal_api.routes.auth._set_pkce_pending")

        response = client.get("/api/auth/callback?error=access_denied&error_description=User+denied+access")
        assert response.status_code == 400
        assert b"User denied access" in response.data

    def test_callback_token_exchange_failure(self, client, mocker, tmp_path):
        """Test callback returns error when token exchange fails."""
        mock_session = MagicMock()
        mock_session.complete_pkce_login.return_value = False
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", tmp_path / "session.json")

        response = client.get("/api/auth/callback?code=bad_code")
        assert response.status_code == 401
        assert b"Token exchange failed" in response.data

    def test_callback_clears_pending_on_success(self, client, mocker, tmp_path):
        """Test that _pkce_pending is cleared after successful callback."""
        mock_session = MagicMock()
        mock_session.complete_pkce_login.return_value = True
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", tmp_path / "session.json")

        # Set pending before callback
        from tidal_api.routes.auth import _is_pkce_pending, _set_pkce_pending

        _set_pkce_pending(True)
        assert _is_pkce_pending()

        client.get("/api/auth/callback?code=test_code")

        assert not _is_pkce_pending()

    def test_callback_clears_pending_on_failure(self, client, mocker, tmp_path):
        """Test that _pkce_pending is cleared even when callback fails."""
        mock_session = MagicMock()
        mock_session.complete_pkce_login.return_value = False
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", tmp_path / "session.json")

        from tidal_api.routes.auth import _is_pkce_pending, _set_pkce_pending

        _set_pkce_pending(True)

        client.get("/api/auth/callback?code=bad_code")

        assert not _is_pkce_pending()


class TestAuthStatusEndpoint:
    """Tests for /api/auth/status endpoint."""

    def test_status_no_session_file(self, client, mocker):
        """Test status returns unauthenticated when no session file exists."""
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", MagicMock(exists=MagicMock(return_value=False)))

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False

    def test_status_valid_session(self, client, mock_session_file, mocker):
        """Test status returns authenticated with valid session."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.id = 12345
        mock_session.user.username = "testuser"
        mock_session.user.email = "test@example.com"
        mocker.patch("tidal_api.routes.auth.BrowserSession", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", mock_session_file)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is True
        assert data["user"]["id"] == 12345
