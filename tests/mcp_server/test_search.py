"""Tests for search_tidal MCP tool."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestSearchTidal:
    """Tests for search_tidal MCP tool."""

    def test_search_not_authenticated(self, mock_auth_failure):
        """Test search when not authenticated."""
        from tools.search import search_tidal

        result = search_tidal("test query")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_search_empty_query(self, mocker):
        """Test search with empty query."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.search import search_tidal

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

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.search import search_tidal

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

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.search import search_tidal

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

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.search import search_tidal

        result = search_tidal("test", limit=30)

        assert result["status"] == "success"
        assert captured_params.get("limit") == 30
