"""Tests for AlbumsEndpoint"""
import pytest
import responses

from tidal_client.config import Config
from tidal_client.endpoints.albums import AlbumsEndpoint
from tidal_client.session import TidalSession


def _make_session(token: str = "test_token") -> tuple[TidalSession, AlbumsEndpoint]:
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = token
    return session, AlbumsEndpoint(session)


def test_albums_endpoint_init():
    """AlbumsEndpoint should initialize with session"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    assert AlbumsEndpoint(session).session == session


@responses.activate
def test_get_album_returns_album_dict():
    """get() should return album data from API"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456",
        json={
            "id": "456",
            "title": "Test Album",
            "cover": "cover-uuid",
            "numberOfTracks": 10,
            "popularity": 80,
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get("456")
    assert result["id"] == "456"
    assert result["title"] == "Test Album"
    assert result["numberOfTracks"] == 10


@responses.activate
def test_get_album_includes_authorization():
    """get() should include Bearer token in request"""
    responses.add(responses.GET, "https://api.tidal.com/v1/albums/456", json={"id": "456"}, status=200)
    _, endpoint = _make_session("my_test_token")
    endpoint.get("456")
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_test_token"


@responses.activate
def test_get_tracks_returns_track_list():
    """get_tracks() should return list of track dicts from items"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/tracks",
        json={
            "items": [
                {"id": "t1", "title": "Track One"},
                {"id": "t2", "title": "Track Two"},
            ],
            "totalNumberOfItems": 2,
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_tracks("456")
    assert len(result) == 2
    assert result[0]["id"] == "t1"
    assert result[1]["title"] == "Track Two"


@responses.activate
def test_get_tracks_passes_limit_and_offset():
    """get_tracks() should forward limit and offset params"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/tracks",
        json={"items": [], "totalNumberOfItems": 0},
        status=200,
    )
    _, endpoint = _make_session()
    endpoint.get_tracks("456", limit=25, offset=10)
    url = responses.calls[0].request.url
    assert "limit=25" in url
    assert "offset=10" in url


@responses.activate
def test_get_tracks_returns_empty_list_when_no_items():
    """get_tracks() should return empty list when items key is missing"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/tracks",
        json={},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_tracks("456")
    assert result == []


@responses.activate
def test_get_similar_returns_album_list():
    """get_similar() should return list of similar album dicts"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/similar",
        json={
            "items": [
                {"id": "789", "title": "Similar Album"},
            ],
            "totalNumberOfItems": 1,
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_similar("456")
    assert len(result) == 1
    assert result[0]["id"] == "789"
    assert result[0]["title"] == "Similar Album"


@responses.activate
def test_get_similar_returns_empty_list_when_no_items():
    """get_similar() should return empty list when items key is missing"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/similar",
        json={},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_similar("456")
    assert result == []


@responses.activate
def test_get_review_returns_text():
    """get_review() should return the review text string"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/review",
        json={"text": "A groundbreaking album.", "summary": "Groundbreaking."},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_review("456")
    assert result == "A groundbreaking album."


@responses.activate
def test_get_review_returns_none_when_missing():
    """get_review() should return None when no text in response"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/albums/456/review",
        json={},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_review("456")
    assert result is None


@responses.activate
def test_get_album_raises_not_found_on_404():
    """get() should raise NotFoundError when API returns 404"""
    from tidal_client.exceptions import NotFoundError

    responses.add(responses.GET, "https://api.tidal.com/v1/albums/000", status=404, json={"error": "not found"})
    _, endpoint = _make_session()
    with pytest.raises(NotFoundError):
        endpoint.get("000")
