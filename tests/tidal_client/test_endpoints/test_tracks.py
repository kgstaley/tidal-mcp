"""Tests for TracksEndpoint"""
import pytest
import responses

from tidal_client.config import Config
from tidal_client.endpoints.tracks import TracksEndpoint
from tidal_client.exceptions import NotFoundError
from tidal_client.session import TidalSession


def _make_session(token: str = "test_token") -> tuple[TidalSession, TracksEndpoint]:
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = token
    return session, TracksEndpoint(session)


def test_tracks_endpoint_init():
    """TracksEndpoint should initialize with session"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    assert TracksEndpoint(session).session == session


@responses.activate
def test_get_track_returns_track_dict():
    """get() should return track data from API"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123",
        json={
            "id": "123",
            "title": "Test Track",
            "duration": 240,
            "trackNumber": 3,
            "popularity": 65,
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get("123")
    assert result["id"] == "123"
    assert result["title"] == "Test Track"
    assert result["duration"] == 240
    assert result["trackNumber"] == 3


@responses.activate
def test_get_track_includes_authorization():
    """get() should include Bearer token in request"""
    responses.add(responses.GET, "https://api.tidal.com/v1/tracks/123", json={"id": "123"}, status=200)
    _, endpoint = _make_session("my_test_token")
    endpoint.get("123")
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_test_token"


@responses.activate
def test_get_track_raises_not_found_on_404():
    """get() should raise NotFoundError when API returns 404"""
    responses.add(responses.GET, "https://api.tidal.com/v1/tracks/000", status=404, json={"error": "not found"})
    _, endpoint = _make_session()
    with pytest.raises(NotFoundError):
        endpoint.get("000")


@responses.activate
def test_get_lyrics_returns_lyrics_dict():
    """get_lyrics() should return dict with text, subtitles, provider keys"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/lyrics",
        json={
            "text": "Some lyrics here",
            "subtitles": "[00:00.00]Some lyrics here",
            "provider": "Musixmatch",
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_lyrics("123")
    assert result is not None
    assert result["text"] == "Some lyrics here"
    assert result["subtitles"] == "[00:00.00]Some lyrics here"
    assert result["provider"] == "Musixmatch"


@responses.activate
def test_get_lyrics_returns_none_on_404():
    """get_lyrics() should return None when API returns 404 (no lyrics available)"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/lyrics",
        status=404,
        json={"error": "not found"},
    )
    _, endpoint = _make_session()
    result = endpoint.get_lyrics("123")
    assert result is None


@responses.activate
def test_get_lyrics_returns_none_when_text_missing():
    """get_lyrics() should return None when text key is absent from response"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/lyrics",
        json={},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_lyrics("123")
    assert result is None


@responses.activate
def test_get_recommendations_returns_track_list():
    """get_recommendations() should return list of track dicts from items"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/recommendations",
        json={
            "items": [
                {"id": "456", "title": "Similar Track One"},
                {"id": "789", "title": "Similar Track Two"},
            ],
            "totalNumberOfItems": 2,
        },
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_recommendations("123")
    assert len(result) == 2
    assert result[0]["id"] == "456"
    assert result[1]["title"] == "Similar Track Two"


@responses.activate
def test_get_recommendations_passes_limit():
    """get_recommendations() should forward limit param"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/recommendations",
        json={"items": [], "totalNumberOfItems": 0},
        status=200,
    )
    _, endpoint = _make_session()
    endpoint.get_recommendations("123", limit=5)
    url = responses.calls[0].request.url
    assert "limit=5" in url


@responses.activate
def test_get_recommendations_uses_default_limit():
    """get_recommendations() should use default limit of 10"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/recommendations",
        json={"items": [], "totalNumberOfItems": 0},
        status=200,
    )
    _, endpoint = _make_session()
    endpoint.get_recommendations("123")
    url = responses.calls[0].request.url
    assert "limit=10" in url


@responses.activate
def test_get_recommendations_returns_empty_list_when_no_items():
    """get_recommendations() should return empty list when items key is missing"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/123/recommendations",
        json={},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_recommendations("123")
    assert result == []


@responses.activate
def test_get_recommendations_returns_empty_list_on_404():
    """get_recommendations() should return empty list when API returns 404"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/tracks/000/recommendations",
        status=404,
        json={"error": "not found"},
    )
    _, endpoint = _make_session()
    result = endpoint.get_recommendations("000")
    assert result == []


def test_session_tracks_property_returns_endpoint():
    """session.tracks should return TracksEndpoint instance"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    tracks = session.tracks
    assert isinstance(tracks, TracksEndpoint)


def test_session_tracks_property_caches_instance():
    """session.tracks should return same instance on repeated access"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    tracks_first = session.tracks
    tracks_second = session.tracks
    assert tracks_first is tracks_second
