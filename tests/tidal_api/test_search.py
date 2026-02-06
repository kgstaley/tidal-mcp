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
