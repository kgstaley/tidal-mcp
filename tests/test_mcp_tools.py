"""Unit tests for mcp_server/server.py MCP tools."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_server"))

# Import the real utils module first to get the actual helper functions
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mcp_utils_real",
    Path(__file__).parent.parent / "mcp_server" / "utils.py"
)
mcp_utils_real = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_utils_real)

# Mock the utils module before importing server, but use real helper functions
mock_utils = MagicMock()
mock_utils.start_flask_app = MagicMock()
mock_utils.shutdown_flask_app = MagicMock()
mock_utils.FLASK_APP_URL = "http://localhost:5050"
mock_utils.FLASK_PORT = 5050
# Use real implementations for helper functions
mock_utils.error_response = mcp_utils_real.error_response
mock_utils.check_tidal_auth = mcp_utils_real.check_tidal_auth
mock_utils.handle_api_response = mcp_utils_real.handle_api_response
mock_utils.validate_list = mcp_utils_real.validate_list
mock_utils.validate_string = mcp_utils_real.validate_string
sys.modules["utils"] = mock_utils


class MockResponse:
    """Mock requests.Response object."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


@pytest.fixture
def mock_auth_success(mocker):
    """Mock successful authentication check."""
    def auth_side_effect(url, **kwargs):
        if "/api/auth/status" in url:
            return MockResponse({"authenticated": True})
        return MockResponse({}, 404)

    return mocker.patch("requests.get", side_effect=auth_side_effect)


@pytest.fixture
def mock_auth_failure(mocker):
    """Mock failed authentication check."""
    def auth_side_effect(url, **kwargs):
        if "/api/auth/status" in url:
            return MockResponse({"authenticated": False})
        return MockResponse({}, 404)

    return mocker.patch("requests.get", side_effect=auth_side_effect)


class TestSearchTidal:
    """Tests for search_tidal MCP tool."""

    def test_search_not_authenticated(self, mock_auth_failure):
        """Test search when not authenticated."""
        # Import here to use mocked modules
        from server import search_tidal

        result = search_tidal("test query")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_search_empty_query(self, mocker):
        """Test search with empty query."""
        mocker.patch(
            "requests.get",
            return_value=MockResponse({"authenticated": True}),
        )

        from server import search_tidal

        result = search_tidal("")

        assert result["status"] == "error"
        assert "query" in result["message"].lower()

    def test_search_success(self, mocker):
        """Test successful search."""
        search_results = {
            "query": "test",
            "artists": [{"id": 1, "name": "Artist 1"}],
            "tracks": [{"id": 2, "title": "Track 1"}],
            "albums": [{"id": 3, "name": "Album 1"}],
            "playlists": [],
            "videos": [],
            "top_hit": {"type": "artist", "data": {"id": 1, "name": "Artist 1"}},
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/search" in url:
                return MockResponse(search_results)
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)

        from server import search_tidal

        result = search_tidal("test")

        assert result["status"] == "success"
        assert result["query"] == "test"
        assert len(result["artists"]) == 1
        assert len(result["tracks"]) == 1
        assert len(result["albums"]) == 1
        assert result["top_hit"] is not None

    def test_search_with_types(self, mocker):
        """Test search with specific types."""
        search_results = {
            "query": "test",
            "artists": [{"id": 1, "name": "Artist 1"}],
            "tracks": [],
            "albums": [],
            "playlists": [],
            "videos": [],
        }

        captured_params = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/search" in url:
                captured_params.update(kwargs.get("params", {}))
                return MockResponse(search_results)
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)

        from server import search_tidal

        result = search_tidal("test", types=["artists", "tracks"])

        assert result["status"] == "success"
        assert "types" in captured_params
        assert "artists" in captured_params["types"]

    def test_search_with_limit(self, mocker):
        """Test search with custom limit."""
        search_results = {
            "query": "test",
            "artists": [],
            "tracks": [],
            "albums": [],
            "playlists": [],
            "videos": [],
        }

        captured_params = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/search" in url:
                captured_params.update(kwargs.get("params", {}))
                return MockResponse(search_results)
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)

        from server import search_tidal

        result = search_tidal("test", limit=30)

        assert result["status"] == "success"
        assert captured_params.get("limit") == 30


class TestAddTracksToPlaylist:
    """Tests for add_tracks_to_playlist MCP tool."""

    def test_add_tracks_not_authenticated(self, mock_auth_failure):
        """Test adding tracks when not authenticated."""
        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist("playlist-123", ["track-1"])

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_add_tracks_no_playlist_id(self, mocker):
        """Test adding tracks without playlist ID."""
        mocker.patch(
            "requests.get",
            return_value=MockResponse({"authenticated": True}),
        )

        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist("", ["track-1"])

        assert result["status"] == "error"
        assert "playlist" in result["message"].lower()

    def test_add_tracks_no_track_ids(self, mocker):
        """Test adding tracks without track IDs."""
        mocker.patch(
            "requests.get",
            return_value=MockResponse({"authenticated": True}),
        )

        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist("playlist-123", [])

        assert result["status"] == "error"
        assert "track" in result["message"].lower()

    def test_add_tracks_success(self, mocker):
        """Test successfully adding tracks."""
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch(
            "requests.post",
            return_value=MockResponse({
                "status": "success",
                "message": "Added 2 tracks to playlist",
                "added_count": 2,
            }),
        )

        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist("playlist-123", ["track-1", "track-2"])

        assert result["status"] == "success"
        assert result["added_count"] == 2
        assert "playlist_url" in result

    def test_add_tracks_playlist_not_found(self, mocker):
        """Test adding tracks to non-existent playlist."""
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch(
            "requests.post",
            return_value=MockResponse({"error": "Playlist not found"}, 404),
        )

        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist("invalid-playlist", ["track-1"])

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_add_tracks_with_options(self, mocker):
        """Test adding tracks with allow_duplicates and position."""
        captured_payload = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        def mock_post(url, **kwargs):
            captured_payload.update(kwargs.get("json", {}))
            return MockResponse({
                "status": "success",
                "message": "Added tracks",
                "added_count": 1,
            })

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch("requests.post", side_effect=mock_post)

        from server import add_tracks_to_playlist

        result = add_tracks_to_playlist(
            "playlist-123",
            ["track-1"],
            allow_duplicates=True,
            position=5,
        )

        assert result["status"] == "success"
        assert captured_payload.get("allow_duplicates") is True
        assert captured_payload.get("position") == 5


class TestRemoveTracksFromPlaylist:
    """Tests for remove_tracks_from_playlist MCP tool."""

    def test_remove_tracks_not_authenticated(self, mock_auth_failure):
        """Test removing tracks when not authenticated."""
        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("playlist-123", ["track-1"])

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_remove_tracks_no_playlist_id(self, mocker):
        """Test removing tracks without playlist ID."""
        mocker.patch(
            "requests.get",
            return_value=MockResponse({"authenticated": True}),
        )

        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("", ["track-1"])

        assert result["status"] == "error"
        assert "playlist" in result["message"].lower()

    def test_remove_tracks_no_track_ids(self, mocker):
        """Test removing tracks without track IDs."""
        mocker.patch(
            "requests.get",
            return_value=MockResponse({"authenticated": True}),
        )

        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("playlist-123", [])

        assert result["status"] == "error"
        assert "track" in result["message"].lower()

    def test_remove_tracks_success(self, mocker):
        """Test successfully removing tracks."""
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch(
            "requests.delete",
            return_value=MockResponse({
                "status": "success",
                "message": "Removed 2 tracks from playlist",
                "removed_count": 2,
            }),
        )

        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("playlist-123", ["track-1", "track-2"])

        assert result["status"] == "success"
        assert result["removed_count"] == 2
        assert "playlist_url" in result

    def test_remove_tracks_playlist_not_found(self, mocker):
        """Test removing tracks from non-existent playlist."""
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch(
            "requests.delete",
            return_value=MockResponse({"error": "Playlist not found"}, 404),
        )

        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("invalid-playlist", ["track-1"])

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_remove_tracks_forbidden(self, mocker):
        """Test removing tracks from someone else's playlist."""
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch("requests.get", side_effect=mock_get)
        mocker.patch(
            "requests.delete",
            return_value=MockResponse({"error": "Cannot modify this playlist"}, 403),
        )

        from server import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("not-my-playlist", ["track-1"])

        assert result["status"] == "error"
        assert "cannot modify" in result["message"].lower() or "own playlists" in result["message"].lower()
