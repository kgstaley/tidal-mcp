"""Tests for /api/search Flask endpoint."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockAlbum, MockArtist, MockPlaylist, MockTrack, MockVideo


def mock_search_results():
    """Return a dict matching tidalapi.SearchResults TypedDict."""
    return {
        "artists": [MockArtist()],
        "tracks": [MockTrack()],
        "albums": [MockAlbum()],
        "playlists": [MockPlaylist()],
        "videos": [MockVideo()],
        "top_hit": None,
    }


class TestSearchEndpoint:
    """Tests for /api/search endpoint."""

    def test_search_missing_query(self, client, mock_session_file, mocker):
        """Test search with missing query parameter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/search")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "query" in data["error"].lower()

    def test_search_success(self, client, mock_session_file, mocker):
        """Test successful search."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.search.return_value = mock_search_results()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/search?query=test")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["query"] == "test"
        assert "artists" in data
        assert "tracks" in data
        assert "albums" in data
        assert "playlists" in data
        assert "videos" in data
        assert "top_hit" not in data

    def test_search_with_types_filter(self, client, mock_session_file, mocker):
        """Test search with specific types filter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.search.return_value = mock_search_results()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/search?query=test&types=artists,tracks")
        assert response.status_code == 200

        mock_session.search.assert_called_once()
        call_args = mock_session.search.call_args
        assert call_args[0][0] == "test"
        assert call_args[1]["models"] is not None

    def test_search_with_limit(self, client, mock_session_file, mocker):
        """Test search with custom limit."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.search.return_value = mock_search_results()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/search?query=test&limit=30")
        assert response.status_code == 200

        mock_session.search.assert_called_once()
        call_args = mock_session.search.call_args
        assert call_args[1]["limit"] == 30

    def test_search_unauthorized(self, client):
        """Test search without authentication."""
        response = client.get("/api/search?query=test")
        assert response.status_code == 401


class TestSearchCustomClient:
    """Tests for /api/search with TIDAL_USE_CUSTOM_CLIENT=true."""

    def test_search_returns_all_types_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client search returns all result types."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")

        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.search.search.return_value = {
            "artists": [{"id": "1", "name": "Test Artist", "picture": None}],
            "tracks": [
                {
                    "id": 2,
                    "title": "Test Track",
                    "duration": 180,
                    "explicit": False,
                    "artist": {"id": "1", "name": "Test Artist"},
                    "album": {"id": 3, "title": "Test Album"},
                }
            ],
            "albums": [
                {
                    "id": 3,
                    "title": "Test Album",
                    "cover": None,
                    "explicit": False,
                    "artist": {"id": "1", "name": "Test Artist"},
                }
            ],
            "playlists": [{"uuid": "abc-123", "title": "Test Playlist", "numberOfTracks": 5}],
            "videos": [
                {
                    "id": 5,
                    "title": "Test Video",
                    "duration": 300,
                    "explicit": False,
                    "artist": {"id": "1", "name": "Test Artist"},
                }
            ],
        }
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)

        response = client.get("/api/search?query=test")
        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == "test"
        assert len(data["artists"]) == 1
        assert len(data["tracks"]) == 1
        assert len(data["albums"]) == 1
        assert len(data["playlists"]) == 1
        assert len(data["videos"]) == 1

    def test_search_with_types_filter_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client search respects types filter."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")

        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.search.search.return_value = {
            "artists": [{"id": "1", "name": "Test Artist", "picture": None}],
            "tracks": [],
            "albums": [],
            "playlists": [],
            "videos": [],
        }
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)

        response = client.get("/api/search?query=test&types=artists")
        assert response.status_code == 200
        # Verify search was called with types filter
        mock_custom_session.search.search.assert_called_once_with("test", types=["artists"], limit=20)

    def test_search_missing_query_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client returns 400 when query param missing."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")

        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)

        response = client.get("/api/search")
        assert response.status_code == 400

    def test_search_not_authenticated_custom_client(self, client, monkeypatch):
        """Returns 401 when not authenticated."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        response = client.get("/api/search?query=test")
        assert response.status_code == 401
