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


class TestGetUserMixesCustomClient:
    """Tests for GET /api/mixes with TIDAL_USE_CUSTOM_CLIENT=true."""

    def test_get_user_mixes_success_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Test successfully fetching user mixes via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")
        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.mixes.get_user_mixes.return_value = [
            {
                "id": "mix-1",
                "title": "Daily Mix 1",
                "subTitle": "Based on your plays",
                "shortSubtitle": "Daily",
                "mixType": "DAILY_MIX",
                "images": None,
            },
            {
                "id": "mix-2",
                "title": "Discovery Mix",
                "subTitle": "New music",
                "shortSubtitle": "Discovery",
                "mixType": "DISCOVERY_MIX",
                "images": None,
            },
        ]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)
        response = client.get("/api/mixes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 2
        assert len(data["mixes"]) == 2
        assert data["mixes"][0]["id"] == "mix-1"
        assert data["mixes"][1]["id"] == "mix-2"

    def test_get_user_mixes_empty_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Test fetching user mixes returns empty list via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")
        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.mixes.get_user_mixes.return_value = []
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)
        response = client.get("/api/mixes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["mixes"] == []

    def test_get_user_mixes_not_authenticated_custom_client(self, client, monkeypatch):
        """Test fetching user mixes when not authenticated via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        response = client.get("/api/mixes")
        assert response.status_code == 401


class TestGetMixTracksCustomClient:
    """Tests for GET /api/mixes/<id>/tracks with TIDAL_USE_CUSTOM_CLIENT=true."""

    def test_get_mix_tracks_success_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Test successfully fetching mix tracks via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")
        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.mixes.get_mix_tracks.return_value = [
            {
                "id": 1,
                "title": "Track One",
                "duration": 200,
                "artist": {"id": "a1", "name": "Artist A"},
                "album": {"id": "al1", "title": "Album A"},
            },
            {
                "id": 2,
                "title": "Track Two",
                "duration": 180,
                "artist": {"id": "a2", "name": "Artist B"},
                "album": {"id": "al2", "title": "Album B"},
            },
        ]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)
        response = client.get("/api/mixes/mix-1/tracks")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 2
        assert len(data["tracks"]) == 2
        mock_custom_session.mixes.get_mix_tracks.assert_called_once_with("mix-1")

    def test_get_mix_tracks_empty_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Test fetching mix tracks returns empty list when mix not found via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        monkeypatch.setenv("TIDAL_CLIENT_ID", "test_id")
        monkeypatch.setenv("TIDAL_CLIENT_SECRET", "test_secret")
        mock_custom_session = MagicMock()
        mock_custom_session._is_token_valid.return_value = True
        mock_custom_session.mixes.get_mix_tracks.return_value = []
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_custom_session)
        response = client.get("/api/mixes/missing-mix/tracks")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["tracks"] == []

    def test_get_mix_tracks_not_authenticated_custom_client(self, client, monkeypatch):
        """Test fetching mix tracks when not authenticated via custom client."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        response = client.get("/api/mixes/mix-1/tracks")
        assert response.status_code == 401
