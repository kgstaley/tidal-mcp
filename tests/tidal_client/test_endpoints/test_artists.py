"""Tests for ArtistsEndpoint"""
import responses

from tidal_client.config import Config
from tidal_client.endpoints.artists import ArtistsEndpoint
from tidal_client.session import TidalSession


def test_artists_endpoint_init():
    """ArtistsEndpoint should initialize with session"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)

    endpoint = ArtistsEndpoint(session)

    assert endpoint.session == session


@responses.activate
def test_get_artist_returns_artist_dict():
    """get() should return artist data from API"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={
            "id": "123",
            "name": "Test Artist",
            "picture": "artist-uuid",
            "popularity": 85
        },
        status=200
    )

    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = "test_token"

    endpoint = ArtistsEndpoint(session)
    result = endpoint.get("123")

    assert result["id"] == "123"
    assert result["name"] == "Test Artist"
    assert result["picture"] == "artist-uuid"
    assert result["popularity"] == 85


@responses.activate
def test_get_artist_includes_authorization():
    """get() should include Bearer token in request"""
    responses.add(
        responses.GET,
        "https://api.tidal.com/v1/artists/123",
        json={"id": "123", "name": "Test Artist"},
        status=200
    )

    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = "my_test_token"

    endpoint = ArtistsEndpoint(session)
    endpoint.get("123")

    # Verify Authorization header was sent
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.headers["Authorization"] == "Bearer my_test_token"
