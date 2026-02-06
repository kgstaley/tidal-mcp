"""Tests for favorites MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetFavorites:
    """Tests for get_favorites MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.favorites import get_favorites

        result = get_favorites("artists")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_invalid_type(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import get_favorites

        result = get_favorites("invalid")

        assert result["status"] == "error"
        assert "Invalid type" in result["message"]

    def test_empty_type(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import get_favorites

        result = get_favorites("")

        assert result["status"] == "error"
        assert "type" in result["message"].lower()

    def test_artists_success(self, mocker):
        favorites_data = {
            "type": "artists",
            "items": [
                {"id": 1, "name": "Artist 1", "picture_url": None, "url": "https://tidal.com/browse/artist/1"},
            ],
            "total": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/favorites/artists" in url:
                return MockResponse(favorites_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.favorites import get_favorites

        result = get_favorites("artists", limit=10)

        assert result["type"] == "artists"
        assert result["total"] == 1
        assert result["items"][0]["id"] == 1

    def test_tracks_with_order(self, mocker):
        favorites_data = {
            "type": "tracks",
            "items": [{"id": 100, "title": "Track 1"}],
            "total": 1,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/favorites/tracks" in url:
                params = kwargs.get("params", {})
                assert params.get("order") == "NAME"
                assert params.get("order_direction") == "ASC"
                return MockResponse(favorites_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.favorites import get_favorites

        result = get_favorites("tracks", order="NAME", order_direction="ASC")

        assert result["type"] == "tracks"
        assert result["total"] == 1


class TestAddFavorite:
    """Tests for add_favorite MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.favorites import add_favorite

        result = add_favorite("artists", "123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_invalid_type(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import add_favorite

        result = add_favorite("invalid", "123")

        assert result["status"] == "error"
        assert "Invalid type" in result["message"]

    def test_empty_id(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import add_favorite

        result = add_favorite("artists", "")

        assert result["status"] == "error"
        assert "id" in result["message"].lower()

    def test_mixes_error(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import add_favorite

        result = add_favorite("mixes", "mix-1")

        assert result["status"] == "error"
        assert "Cannot add" in result["message"]

    def test_artist_success(self, mocker):
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "post",
            return_value=MockResponse({"status": "success", "type": "artists", "id": "123"}),
        )

        from tools.favorites import add_favorite

        result = add_favorite("artists", "123")

        assert result["status"] == "success"
        assert result["type"] == "artists"
        assert result["id"] == "123"


class TestRemoveFavorite:
    """Tests for remove_favorite MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        from tools.favorites import remove_favorite

        result = remove_favorite("artists", "123")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_id(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import remove_favorite

        result = remove_favorite("artists", "")

        assert result["status"] == "error"
        assert "id" in result["message"].lower()

    def test_mixes_error(self, mocker):
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.favorites import remove_favorite

        result = remove_favorite("mixes", "mix-1")

        assert result["status"] == "error"
        assert "Cannot remove" in result["message"]

    def test_artist_success(self, mocker):
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "delete",
            return_value=MockResponse({"status": "success", "type": "artists", "id": "123"}),
        )

        from tools.favorites import remove_favorite

        result = remove_favorite("artists", "123")

        assert result["status"] == "success"
        assert result["type"] == "artists"
        assert result["id"] == "123"

    def test_track_success(self, mocker):
        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)
        mocker.patch.object(
            mcp_utils_real.http,
            "delete",
            return_value=MockResponse({"status": "success", "type": "tracks", "id": "789"}),
        )

        from tools.favorites import remove_favorite

        result = remove_favorite("tracks", "789")

        assert result["status"] == "success"
        assert result["type"] == "tracks"
        assert result["id"] == "789"
