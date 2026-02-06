"""Tests for /api/artists Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockAlbum, MockArtist, MockTrack


class TestGetArtist:
    """Tests for GET /api/artists/<id> endpoint."""

    def test_get_artist_success(self, client, mock_session_file, mocker):
        """Test successfully fetching artist info."""
        from enum import Enum

        class MockRole(Enum):
            main = "MAIN"
            featured = "FEATURED"

        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist(id=123, name="Test Artist")
        mock_artist.roles = [MockRole.main, MockRole.featured]
        mock_artist.get_bio = MagicMock(return_value="A great artist biography.")
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["id"] == 123
        assert data["name"] == "Test Artist"
        assert data["bio"] == "A great artist biography."
        assert data["roles"] == ["MAIN", "FEATURED"]
        assert "url" in data
        assert "picture_url" in data

    def test_get_artist_not_found(self, client, mock_session_file, mocker):
        """Test fetching non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999")
        assert response.status_code == 404

    def test_get_artist_bio_unavailable(self, client, mock_session_file, mocker):
        """Test artist with no bio available."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.roles = []
        mock_artist.get_bio = MagicMock(side_effect=Exception("Bio not available"))
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["bio"] is None

    def test_get_artist_not_authenticated(self, client):
        """Test fetching artist when not authenticated."""
        response = client.get("/api/artists/123")
        assert response.status_code == 401


class TestGetArtistTopTracks:
    """Tests for GET /api/artists/<id>/top-tracks endpoint."""

    def test_top_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully fetching top tracks."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_top_tracks = MagicMock(
            return_value=[MockTrack(id=1, name="Hit 1"), MockTrack(id=2, name="Hit 2")]
        )
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/top-tracks")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["artist_id"] == "123"
        assert data["total"] == 2
        assert len(data["tracks"]) == 2

    def test_top_tracks_with_limit(self, client, mock_session_file, mocker):
        """Test top tracks with custom limit."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_top_tracks = MagicMock(return_value=[MockTrack()])
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/top-tracks?limit=5")
        assert response.status_code == 200
        mock_artist.get_top_tracks.assert_called_once_with(limit=5)

    def test_top_tracks_artist_not_found(self, client, mock_session_file, mocker):
        """Test top tracks for non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999/top-tracks")
        assert response.status_code == 404


class TestGetArtistAlbums:
    """Tests for GET /api/artists/<id>/albums endpoint."""

    def test_albums_success(self, client, mock_session_file, mocker):
        """Test successfully fetching artist albums."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_albums = MagicMock(
            return_value=[MockAlbum(id=1, name="Album 1"), MockAlbum(id=2, name="Album 2")]
        )
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/albums")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["artist_id"] == "123"
        assert data["filter"] == "albums"
        assert data["total"] == 2

    def test_albums_ep_singles_filter(self, client, mock_session_file, mocker):
        """Test fetching EP/singles filter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_ep_singles = MagicMock(return_value=[MockAlbum(id=3, name="EP 1")])
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/albums?filter=ep_singles")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["filter"] == "ep_singles"
        assert data["total"] == 1

    def test_albums_invalid_filter(self, client, mock_session_file, mocker):
        """Test albums with invalid filter."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = MockArtist()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/albums?filter=invalid")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "invalid" in data["error"].lower()

    def test_albums_artist_not_found(self, client, mock_session_file, mocker):
        """Test albums for non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999/albums")
        assert response.status_code == 404


class TestGetSimilarArtists:
    """Tests for GET /api/artists/<id>/similar endpoint."""

    def test_similar_success(self, client, mock_session_file, mocker):
        """Test successfully fetching similar artists."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_similar = MagicMock(
            return_value=[MockArtist(id=10, name="Similar 1"), MockArtist(id=11, name="Similar 2")]
        )
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/similar")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["artist_id"] == "123"
        assert data["total"] == 2
        assert len(data["artists"]) == 2

    def test_similar_artist_not_found(self, client, mock_session_file, mocker):
        """Test similar artists for non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999/similar")
        assert response.status_code == 404


class TestGetArtistRadio:
    """Tests for GET /api/artists/<id>/radio endpoint."""

    def test_radio_success(self, client, mock_session_file, mocker):
        """Test successfully fetching artist radio."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        mock_artist.get_radio = MagicMock(
            return_value=[MockTrack(id=100, name="Radio 1"), MockTrack(id=101, name="Radio 2")]
        )
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/radio")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["artist_id"] == "123"
        assert data["total"] == 2
        assert len(data["tracks"]) == 2
        mock_artist.get_radio.assert_called_once_with()

    def test_radio_with_limit_truncates(self, client, mock_session_file, mocker):
        """Test radio with custom limit truncates results."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_artist = MockArtist()
        # get_radio() returns up to 100 tracks (no args in tidalapi v0.8.3)
        mock_artist.get_radio = MagicMock(return_value=[MockTrack(id=i, name=f"Radio {i}") for i in range(10)])
        mock_session.artist.return_value = mock_artist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/123/radio?limit=3")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total"] == 3
        assert len(data["tracks"]) == 3
        # get_radio() called with no args
        mock_artist.get_radio.assert_called_once_with()

    def test_radio_artist_not_found(self, client, mock_session_file, mocker):
        """Test radio for non-existent artist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.artist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/artists/999/radio")
        assert response.status_code == 404
