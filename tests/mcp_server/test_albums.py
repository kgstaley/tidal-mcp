"""Tests for album and track detail MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetAlbumInfo:
    """Tests for get_album_info MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting album info when not authenticated."""
        from tools.albums import get_album_info

        result = get_album_info("456")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_album_id(self, mocker):
        """Test with empty album ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.albums import get_album_info

        result = get_album_info("")

        assert result["status"] == "error"
        assert "album ID" in result["message"]

    def test_success(self, mocker):
        """Test successfully getting album info."""
        album_data = {
            "id": 456,
            "name": "Test Album",
            "artist": "Test Artist",
            "review": "Great album.",
            "audio_quality": "LOSSLESS",
            "url": "https://tidal.com/browse/album/456",
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/albums/456" in url:
                return MockResponse(album_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_info

        result = get_album_info("456")

        assert result["status"] == "success"
        assert result["name"] == "Test Album"
        assert result["review"] == "Great album."

    def test_album_not_found(self, mocker):
        """Test getting info for non-existent album."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_info

        result = get_album_info("999")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestGetAlbumTracks:
    """Tests for get_album_tracks MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.albums import get_album_tracks

        result = get_album_tracks("456")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting album tracks."""
        tracks_data = {
            "album_id": "456",
            "tracks": [{"id": 1, "title": "Track 1"}, {"id": 2, "title": "Track 2"}],
            "total": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/tracks" in url:
                return MockResponse(tracks_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_tracks

        result = get_album_tracks("456")

        assert result["status"] == "success"
        assert result["total"] == 2

    def test_with_custom_limit(self, mocker):
        """Test that limit parameter is passed through."""
        captured_params = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/tracks" in url:
                captured_params.update(kwargs.get("params", {}))
                return MockResponse({"album_id": "456", "tracks": [], "total": 0})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_tracks

        get_album_tracks("456", limit=10)

        assert captured_params.get("limit") == 10


class TestGetSimilarAlbums:
    """Tests for get_similar_albums MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.albums import get_similar_albums

        result = get_similar_albums("456")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting similar albums."""
        similar_data = {
            "album_id": "456",
            "albums": [{"id": 10, "name": "Similar 1"}, {"id": 11, "name": "Similar 2"}],
            "total": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/similar" in url:
                return MockResponse(similar_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_similar_albums

        result = get_similar_albums("456")

        assert result["status"] == "success"
        assert result["total"] == 2
        assert len(result["albums"]) == 2


class TestGetAlbumReview:
    """Tests for get_album_review MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.albums import get_album_review

        result = get_album_review("456")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting album review."""
        review_data = {
            "album_id": "456",
            "review": "An incredible album.",
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/review" in url:
                return MockResponse(review_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_review

        result = get_album_review("456")

        assert result["status"] == "success"
        assert result["review"] == "An incredible album."

    def test_no_review(self, mocker):
        """Test album with no review available."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_album_review

        result = get_album_review("456")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestGetTrackInfo:
    """Tests for get_track_info MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting track info when not authenticated."""
        from tools.albums import get_track_info

        result = get_track_info("789")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_track_id(self, mocker):
        """Test with empty track ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.albums import get_track_info

        result = get_track_info("")

        assert result["status"] == "error"
        assert "track ID" in result["message"]

    def test_success(self, mocker):
        """Test successfully getting track info."""
        track_data = {
            "id": 789,
            "title": "Test Track",
            "artist": "Test Artist",
            "isrc": "USRC12345678",
            "audio_quality": "LOSSLESS",
            "url": "https://tidal.com/browse/track/789?u",
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/tracks/789" in url:
                return MockResponse(track_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_track_info

        result = get_track_info("789")

        assert result["status"] == "success"
        assert result["title"] == "Test Track"
        assert result["isrc"] == "USRC12345678"

    def test_track_not_found(self, mocker):
        """Test getting info for non-existent track."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_track_info

        result = get_track_info("999")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestGetTrackLyrics:
    """Tests for get_track_lyrics MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.albums import get_track_lyrics

        result = get_track_lyrics("789")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting track lyrics."""
        lyrics_data = {
            "track_id": "789",
            "text": "Hello world lyrics",
            "subtitles": "",
            "provider": "Musixmatch",
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/lyrics" in url:
                return MockResponse(lyrics_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_track_lyrics

        result = get_track_lyrics("789")

        assert result["status"] == "success"
        assert result["text"] == "Hello world lyrics"
        assert result["provider"] == "Musixmatch"

    def test_no_lyrics(self, mocker):
        """Test track with no lyrics available."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.albums import get_track_lyrics

        result = get_track_lyrics("999")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
