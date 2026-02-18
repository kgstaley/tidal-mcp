"""Tests for /api/albums and /api/tracks/<id> Flask endpoints."""

import json
from unittest.mock import MagicMock

from tidal_client.exceptions import NotFoundError

from tests.conftest import MockAlbum, MockLyrics, MockTrack


class TestGetAlbum:
    """Tests for GET /api/albums/<id> endpoint."""

    def test_get_album_success(self, client, mock_session_file, mocker):
        """Test successfully fetching album info."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum(id=456, name="Test Album")
        mock_album.review = MagicMock(return_value="A fantastic album.")
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["id"] == 456
        assert data["name"] == "Test Album"
        assert data["review"] == "A fantastic album."
        assert data["audio_quality"] == "LOSSLESS"
        assert data["explicit"] is False
        assert "url" in data
        assert "cover_url" in data

    def test_get_album_not_found(self, client, mock_session_file, mocker):
        """Test fetching non-existent album."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.album.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/999")
        assert response.status_code == 404

    def test_get_album_not_authenticated(self, client):
        """Test fetching album when not authenticated."""
        response = client.get("/api/albums/456")
        assert response.status_code == 401


class TestGetAlbumTracks:
    """Tests for GET /api/albums/<id>/tracks endpoint."""

    def test_album_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully fetching album tracks."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum()
        mock_album.tracks = MagicMock(return_value=[MockTrack(id=1, name="Track 1"), MockTrack(id=2, name="Track 2")])
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456/tracks")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["album_id"] == "456"
        assert data["total"] == 2
        assert len(data["tracks"]) == 2

    def test_album_tracks_with_limit(self, client, mock_session_file, mocker):
        """Test album tracks with custom limit."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum()
        mock_album.tracks = MagicMock(return_value=[MockTrack()])
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456/tracks?limit=10")
        assert response.status_code == 200
        mock_album.tracks.assert_called_once_with(limit=10, offset=0)

    def test_album_tracks_album_not_found(self, client, mock_session_file, mocker):
        """Test album tracks for non-existent album."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.album.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/999/tracks")
        assert response.status_code == 404


class TestGetSimilarAlbums:
    """Tests for GET /api/albums/<id>/similar endpoint."""

    def test_similar_success(self, client, mock_session_file, mocker):
        """Test successfully fetching similar albums."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum()
        mock_album.similar = MagicMock(
            return_value=[MockAlbum(id=10, name="Similar 1"), MockAlbum(id=11, name="Similar 2")]
        )
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456/similar")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["album_id"] == "456"
        assert data["total"] == 2
        assert len(data["albums"]) == 2

    def test_similar_album_not_found(self, client, mock_session_file, mocker):
        """Test similar albums for non-existent album."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.album.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/999/similar")
        assert response.status_code == 404


class TestGetAlbumReview:
    """Tests for GET /api/albums/<id>/review endpoint."""

    def test_review_success(self, client, mock_session_file, mocker):
        """Test successfully fetching album review."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum()
        mock_album.review = MagicMock(return_value="This is a great album review.")
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456/review")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["album_id"] == "456"
        assert data["review"] == "This is a great album review."

    def test_no_review_available(self, client, mock_session_file, mocker):
        """Test album with no review available."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_album = MockAlbum()
        mock_album.review = MagicMock(side_effect=Exception("No review"))
        mock_session.album.return_value = mock_album
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/456/review")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "no review" in data["error"].lower()

    def test_review_album_not_found(self, client, mock_session_file, mocker):
        """Test review for non-existent album."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.album.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/999/review")
        assert response.status_code == 404


class TestGetTrackDetail:
    """Tests for GET /api/tracks/<id> endpoint."""

    def test_get_track_success(self, client, mock_session_file, mocker):
        """Test successfully fetching track detail."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_track = MockTrack(id=789, name="Test Track")
        mock_session.track.return_value = mock_track
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/789")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["id"] == 789
        assert data["title"] == "Test Track"
        assert data["isrc"] == "USRC12345678"
        assert data["audio_quality"] == "LOSSLESS"
        assert data["track_num"] == 1
        assert "url" in data

    def test_get_track_not_found(self, client, mock_session_file, mocker):
        """Test fetching non-existent track."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.track.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/999")
        assert response.status_code == 404

    def test_get_track_not_authenticated(self, client):
        """Test fetching track when not authenticated."""
        response = client.get("/api/tracks/789")
        assert response.status_code == 401


class TestGetTrackLyrics:
    """Tests for GET /api/tracks/<id>/lyrics endpoint."""

    def test_lyrics_success(self, client, mock_session_file, mocker):
        """Test successfully fetching track lyrics."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_track = MockTrack()
        mock_track.lyrics = MagicMock(return_value=MockLyrics(text="Hello world", provider="Musixmatch"))
        mock_session.track.return_value = mock_track
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/789/lyrics")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["track_id"] == "789"
        assert data["text"] == "Hello world"
        assert data["provider"] == "Musixmatch"

    def test_no_lyrics_available(self, client, mock_session_file, mocker):
        """Test track with no lyrics available."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_track = MockTrack()
        mock_track.lyrics = MagicMock(side_effect=Exception("No lyrics"))
        mock_session.track.return_value = mock_track
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/789/lyrics")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "no lyrics" in data["error"].lower()

    def test_lyrics_track_not_found(self, client, mock_session_file, mocker):
        """Test lyrics for non-existent track."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.track.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/999/lyrics")
        assert response.status_code == 404


class TestCustomClientAlbums:
    """Tests for album routes using custom client (TIDAL_USE_CUSTOM_CLIENT=true)."""

    def test_get_album_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_album returns formatted album with review."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.albums.get.return_value = {
            "id": "alb1",
            "title": "Test Album",
            "artist": {"name": "Test Artist"},
            "cover": None,
            "releaseDate": "2024-01-01",
            "numberOfTracks": 10,
            "duration": 3600,
            "explicit": False,
            "popularity": 75,
        }
        mock_session.albums.get_review.return_value = "Great album."
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/alb1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "alb1"
        assert data["name"] == "Test Album"
        assert data["review"] == "Great album."

    def test_get_album_tracks_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_album_tracks returns formatted track list."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.albums.get_tracks.return_value = [
            {
                "id": "t1",
                "title": "Track 1",
                "artist": {"name": "Artist"},
                "album": {"title": "Album"},
                "duration": 240,
            },
        ]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/alb1/tracks")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total"] == 1
        assert data["tracks"][0]["title"] == "Track 1"

    def test_get_album_review_not_found_custom_client(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_album_review returns 404 when review is None."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.albums.get_review.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/albums/alb1/review")
        assert response.status_code == 404


class TestCustomClientTracks:
    """Tests for GET /api/tracks/<id> endpoint using custom client (TIDAL_USE_CUSTOM_CLIENT=true)."""

    def test_get_track_success(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_track returns formatted track data."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.tracks.get.return_value = {
            "id": "trk1",
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
            "album": {"title": "Test Album"},
            "duration": 240,
            "trackNumber": 1,
            "explicit": False,
        }
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/trk1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "trk1"
        assert data["title"] == "Test Track"
        mock_session.tracks.get.assert_called_once_with("trk1")

    def test_get_track_not_found(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_track returns 404 when track not found."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.tracks.get.side_effect = NotFoundError("track not found")
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/trk999")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_get_track_not_authenticated(self, client):
        """Custom client: get_track returns 401 when session file is absent."""
        response = client.get("/api/tracks/trk1")
        assert response.status_code == 401


class TestCustomClientTrackLyrics:
    """Tests for GET /api/tracks/<id>/lyrics endpoint using custom client (TIDAL_USE_CUSTOM_CLIENT=true)."""

    def test_get_track_lyrics_success(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_track_lyrics returns formatted lyrics data."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.tracks.get_lyrics.return_value = {
            "text": "Hello world lyrics",
            "subtitles": "[00:00.00] Hello world",
            "provider": "Musixmatch",
        }
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/trk1/lyrics")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["track_id"] == "trk1"
        assert data["text"] == "Hello world lyrics"
        assert data["provider"] == "Musixmatch"
        mock_session.tracks.get_lyrics.assert_called_once_with("trk1")

    def test_get_track_lyrics_not_found(self, client, mock_session_file, mocker, monkeypatch):
        """Custom client: get_track_lyrics returns 404 when lyrics returns None."""
        monkeypatch.setenv("TIDAL_USE_CUSTOM_CLIENT", "true")
        mock_session = MagicMock()
        mock_session._is_token_valid.return_value = True
        mock_session.tracks.get_lyrics.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/tracks/trk1/lyrics")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "lyrics not found" in data["error"].lower()

    def test_get_track_lyrics_not_authenticated(self, client):
        """Custom client: get_track_lyrics returns 401 when session file is absent."""
        response = client.get("/api/tracks/trk1/lyrics")
        assert response.status_code == 401
