"""Tests for /api/mixes Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockMix, MockTrack


class TestGetUserMixes:
    """Tests for GET /api/mixes endpoint."""

    def test_get_user_mixes_success(self, client, mock_session_file, mocker):
        """Test successfully fetching user mixes."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        # Mock Page object with categories
        mock_page = MagicMock()
        mock_category1 = MagicMock()
        mock_category1.items = [
            MockMix(id="mix-1", title="Daily Mix 1"),
            MockMix(id="mix-2", title="Daily Mix 2"),
        ]
        mock_category2 = MagicMock()
        mock_category2.items = [MockMix(id="mix-3", title="Discovery Mix")]
        mock_page.categories = [mock_category1, mock_category2]

        mock_session.mixes.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/mixes")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 3
        assert len(data["mixes"]) == 3
        assert data["mixes"][0]["id"] == "mix-1"
        assert data["mixes"][0]["title"] == "Daily Mix 1"
        assert data["mixes"][1]["id"] == "mix-2"
        assert data["mixes"][2]["id"] == "mix-3"

    def test_get_user_mixes_empty(self, client, mock_session_file, mocker):
        """Test fetching mixes when none exist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_page = MagicMock()
        mock_page.categories = []
        mock_session.mixes.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/mixes")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 0
        assert data["mixes"] == []

    def test_get_user_mixes_not_authenticated(self, client):
        """Test fetching mixes when not authenticated."""
        response = client.get("/api/mixes")
        assert response.status_code == 401


class TestGetMixTracks:
    """Tests for GET /api/mixes/<id>/tracks endpoint."""

    def test_get_mix_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully fetching mix tracks."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_mix = MockMix(id="mix-1", title="Daily Mix 1")
        mock_mix.items = MagicMock(
            return_value=[
                MockTrack(id=1, name="Track 1"),
                MockTrack(id=2, name="Track 2"),
                MockTrack(id=3, name="Track 3"),
            ]
        )
        mock_session.mix.return_value = mock_mix
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/mixes/mix-1/tracks")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 3
        assert len(data["tracks"]) == 3
        assert data["tracks"][0]["id"] == 1
        assert data["tracks"][0]["title"] == "Track 1"

    def test_get_mix_tracks_with_limit(self, client, mock_session_file, mocker):
        """Test fetching mix tracks with limit parameter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_mix = MockMix(id="mix-1", title="Daily Mix 1")
        mock_mix.items = MagicMock(
            return_value=[
                MockTrack(id=1, name="Track 1"),
                MockTrack(id=2, name="Track 2"),
                MockTrack(id=3, name="Track 3"),
            ]
        )
        mock_session.mix.return_value = mock_mix
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/mixes/mix-1/tracks?limit=2")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 2
        assert len(data["tracks"]) == 2

    def test_get_mix_tracks_not_found(self, client, mock_session_file, mocker):
        """Test fetching tracks from non-existent mix."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.mix.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/mixes/nonexistent/tracks")
        assert response.status_code == 404

    def test_get_mix_tracks_not_authenticated(self, client):
        """Test fetching mix tracks when not authenticated."""
        response = client.get("/api/mixes/mix-1/tracks")
        assert response.status_code == 401
