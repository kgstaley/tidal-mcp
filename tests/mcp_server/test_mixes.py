"""Tests for mix MCP tools."""

from tests.conftest import MockResponse
from tests.mcp_server.conftest import mcp_utils_real


class TestGetUserMixes:
    """Tests for get_user_mixes MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting user mixes when not authenticated."""
        from tools.mixes import get_user_mixes

        result = get_user_mixes()

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_success(self, mocker):
        """Test successfully getting user mixes."""
        mixes_data = {
            "mixes": [
                {
                    "id": "mix-1",
                    "title": "Daily Mix 1",
                    "sub_title": "Daily Mix",
                    "short_subtitle": "Your personalized playlist",
                    "mix_type": "DAILY_MIX",
                    "image_url": "https://example.com/mix1.jpg",
                    "updated": "2024-01-15T12:00:00",
                },
                {
                    "id": "mix-2",
                    "title": "Discovery Mix",
                    "sub_title": "Discovery",
                    "short_subtitle": "New music for you",
                    "mix_type": "DISCOVERY_MIX",
                    "image_url": "https://example.com/mix2.jpg",
                    "updated": "2024-01-16T12:00:00",
                },
            ],
            "count": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/mixes" in url:
                return MockResponse(mixes_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.mixes import get_user_mixes

        result = get_user_mixes()

        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["mixes"]) == 2
        assert result["mixes"][0]["id"] == "mix-1"
        assert result["mixes"][0]["title"] == "Daily Mix 1"


class TestGetMixTracks:
    """Tests for get_mix_tracks MCP tool."""

    def test_not_authenticated(self, mock_auth_failure):
        """Test getting mix tracks when not authenticated."""
        from tools.mixes import get_mix_tracks

        result = get_mix_tracks("mix-1")

        assert result["status"] == "error"
        assert "login" in result["message"].lower()

    def test_empty_mix_id(self, mocker):
        """Test with empty mix ID."""
        mocker.patch.object(
            mcp_utils_real.http,
            "get",
            return_value=MockResponse({"authenticated": True}),
        )

        from tools.mixes import get_mix_tracks

        result = get_mix_tracks("")

        assert result["status"] == "error"
        assert "mix ID" in result["message"]

    def test_success(self, mocker):
        """Test successfully getting mix tracks."""
        tracks_data = {
            "tracks": [
                {
                    "id": 1,
                    "title": "Track 1",
                    "artist": "Artist 1",
                    "album": "Album 1",
                    "duration": 240,
                    "url": "https://tidal.com/browse/track/1?u",
                },
                {
                    "id": 2,
                    "title": "Track 2",
                    "artist": "Artist 2",
                    "album": "Album 2",
                    "duration": 180,
                    "url": "https://tidal.com/browse/track/2?u",
                },
            ],
            "count": 2,
        }

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            if "/api/mixes/mix-1/tracks" in url:
                return MockResponse(tracks_data)
            return MockResponse({}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.mixes import get_mix_tracks

        result = get_mix_tracks("mix-1", limit=50)

        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["tracks"]) == 2
        assert result["tracks"][0]["id"] == 1
        assert result["tracks"][0]["title"] == "Track 1"

    def test_mix_not_found(self, mocker):
        """Test getting tracks for non-existent mix."""

        def mock_get(url, **kwargs):
            if "/api/auth/status" in url:
                return MockResponse({"authenticated": True})
            return MockResponse({"error": "Not found"}, 404)

        mocker.patch.object(mcp_utils_real.http, "get", side_effect=mock_get)

        from tools.mixes import get_mix_tracks

        result = get_mix_tracks("nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
