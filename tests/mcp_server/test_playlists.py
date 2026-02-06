"""Tests for playlist MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestAddTracksToPlaylist:
    """Tests for add_tracks_to_playlist MCP tool."""

    def test_add_tracks_not_authenticated(self, mock_auth_failure):
        """Test adding tracks when not authenticated."""
        from tools.playlists import add_tracks_to_playlist

        result = add_tracks_to_playlist("playlist-123", ["track-1"])

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_add_tracks_no_playlist_id(self, mocker):
        """Test adding tracks without playlist ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.playlists import add_tracks_to_playlist

        result = add_tracks_to_playlist("", ["track-1"])

        assert result["status"] == "error"
        assert "playlist" in result["message"].lower()

    def test_add_tracks_no_track_ids(self, mocker):
        """Test adding tracks without track IDs."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.playlists import add_tracks_to_playlist

        result = add_tracks_to_playlist("playlist-123", [])

        assert result["status"] == "error"
        assert "track" in result["message"].lower()

    def test_add_tracks_success(self, mocker):
        """Test successfully adding tracks."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "post",
            return_value=MockResponse(
                {
                    "status": "success",
                    "message": "Added 2 tracks to playlist",
                    "added_count": 2,
                }
            ),
        )

        from tools.playlists import add_tracks_to_playlist

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

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "post",
            return_value=MockResponse({"error": "Playlist not found"}, 404),
        )

        from tools.playlists import add_tracks_to_playlist

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
            return MockResponse(
                {
                    "status": "success",
                    "message": "Added tracks",
                    "added_count": 1,
                }
            )

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(mcp_utils_real.http, "post", side_effect=mock_post)

        from tools.playlists import add_tracks_to_playlist

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
        from tools.playlists import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("playlist-123", ["track-1"])

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_remove_tracks_no_playlist_id(self, mocker):
        """Test removing tracks without playlist ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.playlists import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("", ["track-1"])

        assert result["status"] == "error"
        assert "playlist" in result["message"].lower()

    def test_remove_tracks_no_track_ids(self, mocker):
        """Test removing tracks without track IDs."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.playlists import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("playlist-123", [])

        assert result["status"] == "error"
        assert "track" in result["message"].lower()

    def test_remove_tracks_success(self, mocker):
        """Test successfully removing tracks."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "delete",
            return_value=MockResponse(
                {
                    "status": "success",
                    "message": "Removed 2 tracks from playlist",
                    "removed_count": 2,
                }
            ),
        )

        from tools.playlists import remove_tracks_from_playlist

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

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "delete",
            return_value=MockResponse({"error": "Playlist not found"}, 404),
        )

        from tools.playlists import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("invalid-playlist", ["track-1"])

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_remove_tracks_forbidden(self, mocker):
        """Test removing tracks from someone else's playlist."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "delete",
            return_value=MockResponse({"error": "Cannot modify this playlist"}, 403),
        )

        from tools.playlists import remove_tracks_from_playlist

        result = remove_tracks_from_playlist("not-my-playlist", ["track-1"])

        assert result["status"] == "error"
        assert "cannot modify" in result["message"].lower() or "own playlists" in result["message"].lower()
