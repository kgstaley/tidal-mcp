"""Tests for /api/playlists Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import MockPlaylist


class TestAddTracksToPlaylist:
    """Tests for POST /api/playlists/<playlist_id>/tracks endpoint."""

    def test_add_tracks_missing_body(self, client, mock_session_file, mocker):
        """Test adding tracks without request body (sending empty object)."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_add_tracks_empty_track_ids(self, client, mock_session_file, mocker):
        """Test adding tracks with empty track_ids list."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": []}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_add_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully adding tracks to playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_session.playlist.return_value = mock_playlist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456, 789]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["playlist_id"] == "test-id"
        assert data["added_count"] == 3

    def test_add_tracks_with_options(self, client, mock_session_file, mocker):
        """Test adding tracks with allow_duplicates and position options."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_playlist.add = MagicMock(return_value=[0, 1])
        mock_session.playlist.return_value = mock_playlist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/test-id/tracks",
            data=json.dumps(
                {
                    "track_ids": [123, 456],
                    "allow_duplicates": True,
                    "position": 5,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200

        mock_playlist.add.assert_called_once()
        call_args = mock_playlist.add.call_args
        assert call_args[1]["allow_duplicates"] is True
        assert call_args[1]["position"] == 5

    def test_add_tracks_playlist_not_found(self, client, mock_session_file, mocker):
        """Test adding tracks to non-existent playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.playlist.return_value = None
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/invalid-id/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_add_tracks_not_user_playlist(self, client, mock_session_file, mocker):
        """Test adding tracks to a playlist without add capability."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        class NonUserPlaylist:
            id = "not-user-playlist"
            name = "Not My Playlist"

        mock_session.playlist.return_value = NonUserPlaylist()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.post(
            "/api/playlists/not-user-playlist/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 403


class TestRemoveTracksFromPlaylist:
    """Tests for DELETE /api/playlists/<playlist_id>/tracks endpoint."""

    def test_remove_tracks_missing_body(self, client, mock_session_file, mocker):
        """Test removing tracks without request body (sending empty object)."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_remove_tracks_empty_track_ids(self, client, mock_session_file, mocker):
        """Test removing tracks with empty track_ids list."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": []}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_remove_tracks_success(self, client, mock_session_file, mocker):
        """Test successfully removing tracks from playlist."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()
        mock_session.playlist.return_value = mock_playlist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["playlist_id"] == "test-id"
        assert data["removed_count"] == 2

    def test_remove_tracks_partial_failure(self, client, mock_session_file, mocker):
        """Test removing tracks where some fail."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_playlist = MockPlaylist()

        call_count = [0]

        def remove_side_effect(track_id):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Track not found")

        mock_playlist.remove_by_id = MagicMock(side_effect=remove_side_effect)
        mock_session.playlist.return_value = mock_playlist
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete(
            "/api/playlists/test-id/tracks",
            data=json.dumps({"track_ids": [123, 456, 789]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["removed_count"] == 2
        assert "failed_track_ids" in data
        assert len(data["failed_track_ids"]) == 1

    def test_remove_tracks_not_user_playlist(self, client, mock_session_file, mocker):
        """Test removing tracks from a playlist without remove capability."""
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        class NonUserPlaylist:
            id = "not-user-playlist"
            name = "Not My Playlist"

        mock_session.playlist.return_value = NonUserPlaylist()
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.delete(
            "/api/playlists/not-user-playlist/tracks",
            data=json.dumps({"track_ids": [123]}),
            content_type="application/json",
        )
        assert response.status_code == 403


class TestHealthCheck:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
