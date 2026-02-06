"""Unit tests for tidal_api/app.py Flask endpoints."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tidal_api"))

# Mock browser_session before importing app
sys.modules["browser_session"] = MagicMock()

from app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_session_file(tmp_path, mocker):
    """Create a mock session file."""
    session_file = tmp_path / "tidal-session-oauth.json"
    session_file.write_text("{}")
    mocker.patch("app.SESSION_FILE", session_file)
    return session_file


class MockArtist:
    def __init__(self, id=123, name="Test Artist"):
        self.id = id
        self.name = name

    def picture(self, size):
        return f"https://tidal.com/picture/{self.id}/{size}"


class MockAlbum:
    def __init__(self, id=456, name="Test Album", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.release_date = "2024-01-15"
        self.num_tracks = 12
        self.duration = 3600

    def image(self, size):
        return f"https://tidal.com/image/{self.id}/{size}"


class MockTrack:
    def __init__(self, id=789, name="Test Track", artist=None, album=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.album = album or MockAlbum()
        self.duration = 240


class MockCreator:
    def __init__(self, name="Test User"):
        self.name = name


class MockPlaylist:
    def __init__(self, id="abc-123", name="Test Playlist"):
        self.id = id
        self.name = name
        self.creator = MockCreator()
        self.num_tracks = 25
        self.duration = 5400
        self._tracks = []

    def add(self, track_ids, allow_duplicates=False, position=-1):
        return list(range(len(track_ids)))

    def remove_by_id(self, track_id):
        pass


class MockVideo:
    def __init__(self, id=999, name="Test Video", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.duration = 300


def mock_search_results(include_top_hit=False):
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

        mocker.patch("app.BrowserSession", return_value=mock_session)

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

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.get("/api/search?query=test")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["query"] == "test"
        assert "artists" in data
        assert "tracks" in data
        assert "albums" in data
        assert "playlists" in data
        assert "videos" in data
        # top_hit is optional, verify it's not in response when None
        assert "top_hit" not in data

    def test_search_with_types_filter(self, client, mock_session_file, mocker):
        """Test search with specific types filter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_results = mock_search_results()
        mock_session.search.return_value = mock_results

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.get("/api/search?query=test&types=artists,tracks")
        assert response.status_code == 200

        # Verify search was called with models
        mock_session.search.assert_called_once()
        call_args = mock_session.search.call_args
        assert call_args[0][0] == "test"  # query
        assert call_args[1]["models"] is not None

    def test_search_with_limit(self, client, mock_session_file, mocker):
        """Test search with custom limit."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.search.return_value = mock_search_results()

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.get("/api/search?query=test&limit=30")
        assert response.status_code == 200

        mock_session.search.assert_called_once()
        call_args = mock_session.search.call_args
        assert call_args[1]["limit"] == 30

    def test_search_unauthorized(self, client):
        """Test search without authentication."""
        response = client.get("/api/search?query=test")
        assert response.status_code == 401


class TestAddTracksToPlaylist:
    """Tests for POST /api/playlists/<playlist_id>/tracks endpoint."""

    def test_add_tracks_missing_body(self, client, mock_session_file, mocker):
        """Test adding tracks without request body (sending empty string)."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mocker.patch("app.BrowserSession", return_value=mock_session)

        # Send an empty JSON object body instead of nothing
        response = client.post(
            "/api/playlists/test-id/tracks",
            data="{}",
            content_type="application/json",
        )
        # Empty object has no track_ids, so it should return 400
        assert response.status_code == 400

    def test_add_tracks_empty_track_ids(self, client, mock_session_file, mocker):
        """Test adding tracks with empty track_ids list."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": []}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_add_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully adding tracks to playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_session.playlist.return_value = mock_playlist

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456, 789]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["playlist_id"] == "test-id"
        assert data["added_count"] == 3

    def test_add_tracks_with_options(self, client, mock_session_file, mocker):
        """Test adding tracks with allow_duplicates and position options."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_playlist.add = MagicMock(return_value=[0, 1])
        mock_session.playlist.return_value = mock_playlist

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps(
                {
                    "track_ids": [123, 456],
                    "allow_duplicates": True,
                    "position": 5,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200

        mock_playlist.add.assert_called_once()
        call_args = mock_playlist.add.call_args
        assert call_args[1]["allow_duplicates"] is True
        assert call_args[1]["position"] == 5

    def test_add_tracks_playlist_not_found(self, client, mock_session_file, mocker):
        """Test adding tracks to non-existent playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.playlist.return_value = None

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.post(
            "/api/playlists/invalid-id/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_add_tracks_not_user_playlist(self, client, mock_session_file, mocker):
        """Test adding tracks to a playlist without add capability."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        # Create a playlist object without 'add' method
        class NonUserPlaylist:
            id = "not-user-playlist"
            name = "Not My Playlist"

        mock_session.playlist.return_value = NonUserPlaylist()

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.post(
            "/api/playlists/not-user-playlist/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 403


class TestRemoveTracksFromPlaylist:
    """Tests for DELETE /api/playlists/<playlist_id>/tracks endpoint."""

    def test_remove_tracks_missing_body(self, client, mock_session_file, mocker):
        """Test removing tracks without request body (sending empty object)."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mocker.patch("app.BrowserSession", return_value=mock_session)

        # Send an empty JSON object body instead of nothing
        response = client.delete(
            "/api/playlists/test-id/tracks",
            data="{}",
            content_type="application/json",
        )
        # Empty object has no track_ids, so it should return 400
        assert response.status_code == 400

    def test_remove_tracks_empty_track_ids(self, client, mock_session_file, mocker):
        """Test removing tracks with empty track_ids list."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": []}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_remove_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully removing tracks from playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_session.playlist.return_value = mock_playlist

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["playlist_id"] == "test-id"
        assert data["removed_count"] == 2

    def test_remove_tracks_partial_failure(self, client, mock_session_file, mocker):
        """Test removing tracks where some fail."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()

        # Make remove_by_id fail for second track
        call_count = [0]

        def remove_side_effect(track_id):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Track not found")

        mock_playlist.remove_by_id = MagicMock(side_effect=remove_side_effect)
        mock_session.playlist.return_value = mock_playlist

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456, 789]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have removed 2 out of 3
        assert data["removed_count"] == 2

    def test_remove_tracks_not_user_playlist(self, client, mock_session_file, mocker):
        """Test removing tracks from a playlist without remove capability."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        class NonUserPlaylist:
            id = "not-user-playlist"
            name = "Not My Playlist"

        mock_session.playlist.return_value = NonUserPlaylist()

        mocker.patch("app.BrowserSession", return_value=mock_session)

        response = client.delete(
            "/api/playlists/not-user-playlist/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 403
