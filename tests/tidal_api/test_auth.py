"""Tests for /api/auth Flask endpoints (dual-mode: BrowserSession + custom client)."""

import json
from unittest.mock import MagicMock


class TestAuthStatus:
    """Tests for GET /api/auth/status endpoint."""

    def test_status_no_session_file(self, client):
        """Returns unauthenticated when no session file exists."""
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False
        assert "No session file found" in data["message"]

    def test_status_browser_session_valid(self, client, mock_session_file, mocker):
        """BrowserSession: returns authenticated with user info when session is valid."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.id = 42
        mock_session.user.username = "testuser"
        mock_session.user.email = "test@example.com"
        mocker.patch("tidal_api.routes.auth._create_tidal_session", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", mock_session_file)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is True
        assert data["user"]["id"] == 42
        assert data["user"]["username"] == "testuser"

    def test_status_browser_session_invalid(self, client, mock_session_file, mocker):
        """BrowserSession: returns unauthenticated when session file is invalid."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = False
        mocker.patch("tidal_api.routes.auth._create_tidal_session", return_value=mock_session)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False

    def test_status_custom_client_valid(self, client, mock_session_file, mocker):
        """Custom client: returns authenticated with user_id when token is valid."""
        mock_session = MagicMock(spec=[])  # spec=[] means no attributes → no login_session_file_auto
        mock_session._is_token_valid = MagicMock(return_value=True)
        mock_session._user_id = "user_123"
        mocker.patch("tidal_api.routes.auth._create_tidal_session", return_value=mock_session)
        mocker.patch("tidal_api.routes.auth.SESSION_FILE", mock_session_file)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is True
        assert data["user"]["id"] == "user_123"

    def test_status_custom_client_invalid(self, client, mock_session_file, mocker):
        """Custom client: returns unauthenticated when token is invalid."""
        mock_session = MagicMock(spec=[])  # No login_session_file_auto
        mock_session._is_token_valid = MagicMock(return_value=False)
        mocker.patch("tidal_api.routes.auth._create_tidal_session", return_value=mock_session)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False


class TestRequiresTidalAuth:
    """Tests for requires_tidal_auth decorator with both session types."""

    def test_decorator_custom_client_valid_token(self, client, mock_session_file, mocker):
        """Custom client: route is accessible when token is valid."""
        mock_session = MagicMock(spec=[])  # No login_session_file_auto
        mock_session._is_token_valid = MagicMock(return_value=True)
        mock_session.artist = MagicMock(return_value=MagicMock(id=1, name="Test", picture=None, roles=[]))
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/1")
        # Should not get a 401 - the route returns what mock_session.artist returns
        assert response.status_code != 401

    def test_decorator_custom_client_invalid_token(self, client, mock_session_file, mocker):
        """Custom client: route returns 401 when token is invalid."""
        mock_session = MagicMock(spec=[])  # No login_session_file_auto
        mock_session._is_token_valid = MagicMock(return_value=False)
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/1")
        assert response.status_code == 401

    def test_decorator_browser_session_not_authenticated(self, client):
        """BrowserSession: returns 401 when no session file exists."""
        response = client.get("/api/artists/1")
        assert response.status_code == 401
