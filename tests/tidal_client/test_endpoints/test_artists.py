"""Tests for ArtistsEndpoint"""

import responses

from tidal_client.config import Config
from tidal_client.endpoints.artists import ArtistsEndpoint
from tidal_client.session import TidalSession


def _make_session(token: str = "test_token") -> tuple[TidalSession, ArtistsEndpoint]:
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = token
    return session, ArtistsEndpoint(session)


def test_artists_endpoint_init():
    """ArtistsEndpoint should initialize with session"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    assert ArtistsEndpoint(session).session == session


@responses.activate
def test_get_artist_returns_artist_dict():
    """get() should return artist data from API"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist", "picture": "artist-uuid", "popularity": 85},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get("123")
    assert result["id"] == "123"
    assert result["name"] == "Test Artist"
    assert result["popularity"] == 85


@responses.activate
def test_get_artist_includes_authorization():
    """get() should include Bearer token in request"""
    responses.add(responses.GET, "https://api.tidal.com/v1/artists/123", json={"id": "123"}, status=200)
    _, endpoint = _make_session("my_test_token")
    endpoint.get("123")
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_test_token"


@responses.activate
def test_get_bio_returns_text():
    """get_bio() should return biography text string"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123/bio",
        json={"text": "A legendary artist.", "summary": "A legend."},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_bio("123")
    assert result == "A legendary artist."


@responses.activate
def test_get_bio_returns_none_when_missing():
    """get_bio() should return None when no text in response"""
    responses.add(responses.GET, "https://api.tidal.com/v1/artists/123/bio", json={}, status=200)
    _, endpoint = _make_session()
    assert endpoint.get_bio("123") is None


@responses.activate
def test_get_top_tracks_returns_track_list():
    """get_top_tracks() should return list of track dicts"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123/toptracks",
        json={"items": [{"id": "1", "title": "Track 1"}, {"id": "2", "title": "Track 2"}], "totalNumberOfItems": 2},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_top_tracks("123", limit=10)
    assert len(result) == 2
    assert result[0]["id"] == "1"


@responses.activate
def test_get_albums_uses_filter_param():
    """get_albums() should map filter name to TIDAL API filter value"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123/albums",
        json={"items": [{"id": "alb1", "title": "Album 1"}], "totalNumberOfItems": 1},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_albums("123", filter="ep_singles")
    assert len(result) == 1
    # Verify the API filter param was sent correctly
    assert (
        responses.calls[0].request.url.endswith("filter=EPSSINGLES&limit=50&offset=0")
        or "filter=EPSSINGLES" in responses.calls[0].request.url
    )


@responses.activate
def test_get_similar_returns_artist_list():
    """get_similar() should return list of similar artist dicts"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123/similar",
        json={"items": [{"id": "456", "name": "Similar Artist"}], "totalNumberOfItems": 1},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_similar("123")
    assert len(result) == 1
    assert result[0]["name"] == "Similar Artist"


@responses.activate
def test_get_radio_returns_track_list():
    """get_radio() should return list of radio track dicts"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123/radio",
        json={"items": [{"id": "t1", "title": "Radio Track"}], "totalNumberOfItems": 1},
        status=200,
    )
    _, endpoint = _make_session()
    result = endpoint.get_radio("123")
    assert len(result) == 1
    assert result[0]["title"] == "Radio Track"
