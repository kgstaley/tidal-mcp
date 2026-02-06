"""Tests for discovery MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetForYouPage:
    """Tests for get_for_you_page MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import get_for_you_page

        result = get_for_you_page()
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        page_data = {
            "page_title": "For You",
            "categories": [{"title": "Recommended", "items": [], "count": 0}],
            "category_count": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/for-you" in url:
                return MockResponse(page_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import get_for_you_page

        result = get_for_you_page()
        assert result["status"] == "success"
        assert result["page_title"] == "For You"
        assert result["category_count"] == 1


class TestExploreTidal:
    """Tests for explore_tidal MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import explore_tidal

        result = explore_tidal()
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        page_data = {
            "page_title": "Explore",
            "categories": [{"title": "Trending", "items": [], "count": 0}],
            "category_count": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/explore" in url:
                return MockResponse(page_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import explore_tidal

        result = explore_tidal()
        assert result["status"] == "success"
        assert result["page_title"] == "Explore"
        assert result["category_count"] == 1


class TestGetTidalMoods:
    """Tests for get_tidal_moods MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import get_tidal_moods

        result = get_tidal_moods()
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        moods_data = {
            "moods": [
                {"title": "Chill", "api_path": "pages/moods_chill", "image_id": "img-1"},
                {"title": "Party", "api_path": "pages/moods_party", "image_id": "img-2"},
            ],
            "count": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/moods" in url:
                return MockResponse(moods_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import get_tidal_moods

        result = get_tidal_moods()
        assert result["status"] == "success"
        assert result["count"] == 2
        assert result["moods"][0]["title"] == "Chill"


class TestBrowseTidalMood:
    """Tests for browse_tidal_mood MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import browse_tidal_mood

        result = browse_tidal_mood("pages/moods_chill")
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_api_path(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.discovery import browse_tidal_mood

        result = browse_tidal_mood("")
        assert result["status"] == "error"
        assert "mood API path" in result["message"]

    def test_success(self, mocker):
        page_data = {
            "page_title": "Chill",
            "categories": [{"title": "Chill Playlists", "items": [], "count": 0}],
            "category_count": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/moods/pages/moods_chill" in url:
                return MockResponse(page_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import browse_tidal_mood

        result = browse_tidal_mood("pages/moods_chill")
        assert result["status"] == "success"
        assert result["page_title"] == "Chill"


class TestGetTidalGenres:
    """Tests for get_tidal_genres MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import get_tidal_genres

        result = get_tidal_genres()
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        genres_data = {
            "genres": [
                {"name": "Pop", "path": "pop", "has_playlists": True, "has_artists": True},
                {"name": "Rock", "path": "rock", "has_playlists": True, "has_artists": True},
            ],
            "count": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/genres" in url:
                return MockResponse(genres_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import get_tidal_genres

        result = get_tidal_genres()
        assert result["status"] == "success"
        assert result["count"] == 2
        assert result["genres"][0]["name"] == "Pop"


class TestBrowseTidalGenre:
    """Tests for browse_tidal_genre MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.discovery import browse_tidal_genre

        result = browse_tidal_genre("pop")
        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_genre_path(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.discovery import browse_tidal_genre

        result = browse_tidal_genre("")
        assert result["status"] == "error"
        assert "genre path" in result["message"]

    def test_invalid_content_type(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.discovery import browse_tidal_genre

        result = browse_tidal_genre("pop", content_type="podcasts")
        assert result["status"] == "error"
        assert "Invalid content_type" in result["message"]

    def test_success(self, mocker):
        genre_data = {
            "genre": "pop",
            "content_type": "albums",
            "items": [{"id": 1, "name": "Pop Album"}],
            "count": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/discover/genres/pop/albums" in url:
                return MockResponse(genre_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import browse_tidal_genre

        result = browse_tidal_genre("pop", content_type="albums")
        assert result["status"] == "success"
        assert result["genre"] == "pop"
        assert result["content_type"] == "albums"
        assert result["count"] == 1

    def test_genre_not_found(self, mocker):
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.discovery import browse_tidal_genre

        result = browse_tidal_genre("nonexistent", content_type="albums")
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
