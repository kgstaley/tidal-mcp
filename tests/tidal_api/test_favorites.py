"""Tests for /api/favorites Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockAlbum, MockArtist, MockFavorites, MockMix, MockPlaylist, MockTrack, MockVideo


class TestGetFavorites:
    """Tests for GET /api/favorites/<type> endpoint."""

    def _mock_session_with_favorites(self, mocker, favorites):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.favorites = favorites
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)
        return mock_session

    def test_get_favorite_artists_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._artists = [MockArtist(id=1, name="Artist 1"), MockArtist(id=2, name="Artist 2")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/artists")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "artists"
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == 1
        assert data["items"][0]["name"] == "Artist 1"

    def test_get_favorite_albums_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._albums = [MockAlbum(id=10, name="Album 1")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/albums")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "albums"
        assert data["total"] == 1
        assert data["items"][0]["id"] == 10
        assert data["items"][0]["name"] == "Album 1"

    def test_get_favorite_tracks_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._tracks = [MockTrack(id=100, name="Track 1")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/tracks")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "tracks"
        assert data["total"] == 1
        assert data["items"][0]["id"] == 100
        assert data["items"][0]["title"] == "Track 1"

    def test_get_favorite_videos_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._videos = [MockVideo(id=200, name="Video 1")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/videos")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "videos"
        assert data["total"] == 1
        assert data["items"][0]["id"] == 200
        assert data["items"][0]["title"] == "Video 1"

    def test_get_favorite_playlists_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._playlists = [MockPlaylist(id="pl-1", name="Playlist 1")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/playlists")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "playlists"
        assert data["total"] == 1
        assert data["items"][0]["id"] == "pl-1"
        assert data["items"][0]["title"] == "Playlist 1"

    def test_get_favorite_mixes_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        favorites._mixes = [MockMix(id="mix-1", title="My Mix")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/mixes")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["type"] == "mixes"
        assert data["total"] == 1
        assert data["items"][0]["id"] == "mix-1"
        assert data["items"][0]["title"] == "My Mix"

    def test_get_favorite_tracks_with_order_params(self, client, mock_session_file, mocker):
        favorites = MagicMock()
        favorites.tracks.return_value = [MockTrack(id=100, name="Track 1")]
        self._mock_session_with_favorites(mocker, favorites)

        response = client.get("/api/favorites/tracks?order=NAME&order_direction=ASC&limit=10")
        assert response.status_code == 200

        favorites.tracks.assert_called()
        call_kwargs = favorites.tracks.call_args[1]
        assert call_kwargs["order"] == "NAME"
        assert call_kwargs["order_direction"] == "ASC"

    def test_get_favorites_invalid_type(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/favorites/invalid")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid type" in data["error"]

    def test_get_favorites_not_authenticated(self, client):
        response = client.get("/api/favorites/artists")
        assert response.status_code == 401


class TestAddFavorite:
    """Tests for POST /api/favorites/<type> endpoint."""

    def _mock_session_with_favorites(self, mocker, favorites):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.favorites = favorites
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)
        return mock_session

    def test_add_favorite_artist_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.post("/api/favorites/artists", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["type"] == "artists"
        assert data["id"] == "123"

    def test_add_favorite_album_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.post("/api/favorites/albums", json={"id": 456}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "albums"
        assert data["id"] == "456"

    def test_add_favorite_track_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.post("/api/favorites/tracks", json={"id": "789"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "tracks"

    def test_add_favorite_video_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.post("/api/favorites/videos", json={"id": "999"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "videos"

    def test_add_favorite_playlist_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.post("/api/favorites/playlists", json={"id": "pl-1"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "playlists"

    def test_add_favorite_mixes_returns_400(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post("/api/favorites/mixes", json={"id": "mix-1"}, content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Cannot add" in data["error"]

    def test_add_favorite_invalid_type(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post("/api/favorites/invalid", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid type" in data["error"]

    def test_add_favorite_missing_id(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post("/api/favorites/artists", json={}, content_type="application/json")
        assert response.status_code == 400

    def test_add_favorite_not_authenticated(self, client):
        response = client.post("/api/favorites/artists", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 401


class TestRemoveFavorite:
    """Tests for DELETE /api/favorites/<type> endpoint."""

    def _mock_session_with_favorites(self, mocker, favorites):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.user.favorites = favorites
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)
        return mock_session

    def test_remove_favorite_artist_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.delete("/api/favorites/artists", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "artists"
        assert data["id"] == "123"

    def test_remove_favorite_track_success(self, client, mock_session_file, mocker):
        favorites = MockFavorites()
        self._mock_session_with_favorites(mocker, favorites)

        response = client.delete("/api/favorites/tracks", json={"id": "789"}, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["type"] == "tracks"

    def test_remove_favorite_mixes_returns_400(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete("/api/favorites/mixes", json={"id": "mix-1"}, content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Cannot remove" in data["error"]

    def test_remove_favorite_invalid_type(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete("/api/favorites/invalid", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 400

    def test_remove_favorite_missing_id(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete("/api/favorites/artists", json={}, content_type="application/json")
        assert response.status_code == 400

    def test_remove_favorite_not_authenticated(self, client):
        response = client.delete("/api/favorites/artists", json={"id": "123"}, content_type="application/json")
        assert response.status_code == 401
