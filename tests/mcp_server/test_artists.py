"""Tests for artist MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetArtistInfo:
    """Tests for get_artist_info MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting artist info when not authenticated."""
        from tools.artists import get_artist_info

        result = get_artist_info("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_artist_id(self, mocker):
        """Test with empty artist ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.artists import get_artist_info

        result = get_artist_info("")

        assert result["status"] == "error"
        assert "artist ID" in result["message"]

    def test_success(self, mocker):
        """Test successfully getting artist info."""
        artist_data = {
            "id": 123,
            "name": "Test Artist",
            "bio": "A great artist.",
            "roles": ["Main Artist"],
            "picture_url": "https://example.com/pic.jpg",
            "url": "https://tidal.com/browse/artist/123",
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/artists/123" in url:
                return MockResponse(artist_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_info

        result = get_artist_info("123")

        assert result["status"] == "success"
        assert result["name"] == "Test Artist"
        assert result["bio"] == "A great artist."

    def test_artist_not_found(self, mocker):
        """Test getting info for non-existent artist."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_info

        result = get_artist_info("999")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestGetArtistTopTracks:
    """Tests for get_artist_top_tracks MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.artists import get_artist_top_tracks

        result = get_artist_top_tracks("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting top tracks."""
        top_tracks_data = {
            "artist_id": "123",
            "tracks": [{"id": 1, "title": "Hit 1"}, {"id": 2, "title": "Hit 2"}],
            "total": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/top-tracks" in url:
                return MockResponse(top_tracks_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_top_tracks

        result = get_artist_top_tracks("123", limit=10)

        assert result["status"] == "success"
        assert result["total"] == 2

    def test_with_custom_limit(self, mocker):
        """Test that limit parameter is passed through."""
        captured_params = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/top-tracks" in url:
                captured_params.update(kwargs.get("params", {}))
                return MockResponse({"artist_id": "123", "tracks": [], "total": 0})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_top_tracks

        get_artist_top_tracks("123", limit=5)

        assert captured_params.get("limit") == 5


class TestGetArtistAlbums:
    """Tests for get_artist_albums MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.artists import get_artist_albums

        result = get_artist_albums("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting artist albums."""
        albums_data = {
            "artist_id": "123",
            "filter": "albums",
            "albums": [{"id": 1, "name": "Album 1"}],
            "total": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/albums" in url:
                return MockResponse(albums_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_albums

        result = get_artist_albums("123")

        assert result["status"] == "success"
        assert result["total"] == 1
        assert result["filter"] == "albums"

    def test_with_filter(self, mocker):
        """Test that filter parameter is passed through."""
        captured_params = {}

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/albums" in url:
                captured_params.update(kwargs.get("params", {}))
                return MockResponse({"artist_id": "123", "filter": "ep_singles", "albums": [], "total": 0})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_albums

        get_artist_albums("123", filter="ep_singles")

        assert captured_params.get("filter") == "ep_singles"


class TestGetSimilarArtists:
    """Tests for get_similar_artists MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.artists import get_similar_artists

        result = get_similar_artists("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting similar artists."""
        similar_data = {
            "artist_id": "123",
            "artists": [{"id": 10, "name": "Similar 1"}, {"id": 11, "name": "Similar 2"}],
            "total": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/similar" in url:
                return MockResponse(similar_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_similar_artists

        result = get_similar_artists("123")

        assert result["status"] == "success"
        assert result["total"] == 2
        assert len(result["artists"]) == 2


class TestGetArtistRadio:
    """Tests for get_artist_radio MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test when not authenticated."""
        from tools.artists import get_artist_radio

        result = get_artist_radio("123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting artist radio."""
        radio_data = {
            "artist_id": "123",
            "tracks": [{"id": 100, "title": "Radio Track 1"}],
            "total": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/radio" in url:
                return MockResponse(radio_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.artists import get_artist_radio

        result = get_artist_radio("123", limit=10)

        assert result["status"] == "success"
        assert result["total"] == 1

    def test_empty_artist_id(self, mocker):
        """Test with empty artist ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.artists import get_artist_radio

        result = get_artist_radio("")

        assert result["status"] == "error"
        assert "artist ID" in result["message"]
