"""Tests for /api/discover Flask endpoints."""

import json
from unittest.mock import MagicMock

from tests.conftest import (
    MockAlbum,
    MockArtist,
    MockGenre,
    MockPage,
    MockPageCategory,
    MockPageLink,
    MockTrack,
)


class TestGetForYou:
    """Tests for GET /api/discover/for-you endpoint."""

    def test_success(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        category = MockPageCategory(title="Recommended", items=[MockAlbum(id=1, name="Album 1")])
        mock_page = MockPage(title="For You", categories=[category])
        mock_session.for_you.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/for-you")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["page_title"] == "For You"
        assert data["category_count"] == 1
        assert len(data["categories"]) == 1
        assert data["categories"][0]["title"] == "Recommended"
        assert data["categories"][0]["count"] == 1
        assert data["categories"][0]["items"][0]["type"] == "album"

    def test_empty_categories(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_page = MockPage(title="For You", categories=[])
        mock_session.for_you.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/for-you")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["category_count"] == 0
        assert data["categories"] == []

    def test_null_categories(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_page = MockPage(title="For You", categories=None)
        mock_session.for_you.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/for-you")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["category_count"] == 0

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/for-you")
        assert response.status_code == 401


class TestGetExplore:
    """Tests for GET /api/discover/explore endpoint."""

    def test_success(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        category = MockPageCategory(
            title="Trending",
            items=[MockTrack(id=10, name="Hit Song"), MockArtist(id=20, name="Hot Artist")],
        )
        mock_page = MockPage(title="Explore", categories=[category])
        mock_session.explore.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/explore")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["page_title"] == "Explore"
        assert data["category_count"] == 1
        assert data["categories"][0]["count"] == 2
        types = [item["type"] for item in data["categories"][0]["items"]]
        assert "track" in types
        assert "artist" in types

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/explore")
        assert response.status_code == 401


class TestGetMoods:
    """Tests for GET /api/discover/moods endpoint."""

    def test_success(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        link1 = MockPageLink(title="Chill", api_path="pages/moods_chill")
        link2 = MockPageLink(title="Party", api_path="pages/moods_party")
        category = MockPageCategory(title="Moods", items=[link1, link2])
        mock_page = MockPage(title="Moods", categories=[category])
        mock_session.moods.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/moods")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 2
        assert data["moods"][0]["title"] == "Chill"
        assert data["moods"][0]["api_path"] == "pages/moods_chill"
        assert data["moods"][1]["title"] == "Party"

    def test_empty_moods(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_page = MockPage(title="Moods", categories=[])
        mock_session.moods.return_value = mock_page
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/moods")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 0
        assert data["moods"] == []

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/moods")
        assert response.status_code == 401


class TestBrowseMood:
    """Tests for GET /api/discover/moods/<api_path> endpoint."""

    def test_success(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        category = MockPageCategory(title="Chill Playlists", items=[MockAlbum(id=5, name="Chill Album")])
        mock_page = MockPage(title="Chill", categories=[category])

        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)
        mocker.patch("tidal_api.routes.discovery.Page", return_value=mock_page)

        response = client.get("/api/discover/moods/pages/moods_chill")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["page_title"] == "Chill"
        assert data["category_count"] == 1
        assert data["categories"][0]["title"] == "Chill Playlists"

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/moods/pages/moods_chill")
        assert response.status_code == 401


class TestGetGenres:
    """Tests for GET /api/discover/genres endpoint."""

    def test_success(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_session.genre.get_genres.return_value = [
            MockGenre(name="Pop", path="pop"),
            MockGenre(name="Rock", path="rock", has_videos=True),
        ]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 2
        assert data["genres"][0]["name"] == "Pop"
        assert data["genres"][0]["path"] == "pop"
        assert data["genres"][0]["has_playlists"] is True
        assert data["genres"][1]["name"] == "Rock"
        assert data["genres"][1]["has_videos"] is True

    def test_empty_genres(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_session.genre.get_genres.return_value = []
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["count"] == 0
        assert data["genres"] == []

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/genres")
        assert response.status_code == 401


class TestBrowseGenre:
    """Tests for GET /api/discover/genres/<genre_path>/<content_type> endpoint."""

    def test_success_albums(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_genre = MockGenre(name="Pop", path="pop")
        mock_genre.items = MagicMock(return_value=[MockAlbum(id=1, name="Pop Album")])
        mock_session.genre.get_genres.return_value = [mock_genre]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/pop/albums")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["genre"] == "pop"
        assert data["content_type"] == "albums"
        assert data["count"] == 1
        assert data["items"][0]["name"] == "Pop Album"

    def test_success_artists(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_genre = MockGenre(name="Rock", path="rock")
        mock_genre.items = MagicMock(return_value=[MockArtist(id=2, name="Rock Band")])
        mock_session.genre.get_genres.return_value = [mock_genre]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/rock/artists")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["genre"] == "rock"
        assert data["content_type"] == "artists"
        assert data["count"] == 1
        assert data["items"][0]["name"] == "Rock Band"

    def test_invalid_content_type(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/pop/podcasts")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid content_type" in data["error"]

    def test_genre_not_found(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True
        mock_session.genre.get_genres.return_value = [MockGenre(name="Pop", path="pop")]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/nonexistent/albums")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "not found" in data["error"]

    def test_genre_lacks_content_type(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_genre = MockGenre(name="Pop", path="pop", has_videos=False)
        mock_session.genre.get_genres.return_value = [mock_genre]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/pop/videos")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "does not have" in data["error"]

    def test_genre_type_error(self, client, mock_session_file, mocker):
        mock_session = MagicMock()
        mock_session.login_session_file_auto.return_value = True

        mock_genre = MockGenre(name="Pop", path="pop")
        mock_genre.items = MagicMock(side_effect=TypeError("unsupported"))
        mock_session.genre.get_genres.return_value = [mock_genre]
        mocker.patch("tidal_api.utils._create_tidal_session", return_value=mock_session)

        response = client.get("/api/discover/genres/pop/tracks")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "does not support" in data["error"]

    def test_not_authenticated(self, client):
        response = client.get("/api/discover/genres/pop/albums")
        assert response.status_code == 401
