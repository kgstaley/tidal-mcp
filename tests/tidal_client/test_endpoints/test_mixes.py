"""Tests for MixesEndpoint"""

import pytest
import responses as responses_lib

from tidal_client.config import Config
from tidal_client.endpoints.mixes import MixesEndpoint
from tidal_client.exceptions import NotFoundError
from tidal_client.session import TidalSession

MIXES_PAGE_URL = "https://api.tidal.com/v1/pages/my_collection_my_mixes"
MIX_PAGE_URL = "https://api.tidal.com/v1/pages/mix"


def _make_session(token="test_token"):
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    session._access_token = token
    return session, MixesEndpoint(session)


def _mixes_page_response():
    """Simulated pages/my_collection_my_mixes API response"""
    return {
        "rows": [
            {
                "modules": [
                    {
                        "pagedList": {
                            "items": [
                                {
                                    "id": "mix-1",
                                    "title": "Daily Mix 1",
                                    "subTitle": "Based on your recent plays",
                                    "shortSubtitle": "Daily",
                                    "mixType": "DAILY_MIX",
                                    "images": {
                                        "SMALL": {"url": "https://img.tidal.com/mix-1/320"},
                                        "MEDIUM": {"url": "https://img.tidal.com/mix-1/640"},
                                        "LARGE": {"url": "https://img.tidal.com/mix-1/1500"},
                                    },
                                },
                                {
                                    "id": "mix-2",
                                    "title": "Discovery Mix",
                                    "subTitle": "New music for you",
                                    "shortSubtitle": "Discovery",
                                    "mixType": "DISCOVERY_MIX",
                                    "images": {
                                        "SMALL": {"url": "https://img.tidal.com/mix-2/320"},
                                        "MEDIUM": {"url": "https://img.tidal.com/mix-2/640"},
                                        "LARGE": {"url": "https://img.tidal.com/mix-2/1500"},
                                    },
                                },
                            ]
                        }
                    }
                ]
            }
        ]
    }


def _mix_tracks_response():
    """Simulated pages/mix API response"""
    return {
        "rows": [
            {
                "modules": [
                    {
                        "type": "MIX_HEADER",
                        "mix": {"id": "mix-1", "title": "Daily Mix 1"},
                    }
                ]
            },
            {
                "modules": [
                    {
                        "pagedList": {
                            "items": [
                                {"id": 101, "title": "Track One", "artist": {"id": "1", "name": "Artist A"}},
                                {"id": 102, "title": "Track Two", "artist": {"id": "2", "name": "Artist B"}},
                            ]
                        }
                    }
                ]
            },
        ]
    }


def test_mixes_endpoint_init():
    """MixesEndpoint should initialize with session"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    endpoint = MixesEndpoint(session)
    assert endpoint.session is session


@responses_lib.activate
def test_get_user_mixes_returns_list():
    """get_user_mixes() returns a list of mix dicts"""
    responses_lib.add(responses_lib.GET, MIXES_PAGE_URL, json=_mixes_page_response(), status=200)
    _, endpoint = _make_session()
    result = endpoint.get_user_mixes()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "mix-1"
    assert result[0]["title"] == "Daily Mix 1"
    assert result[1]["id"] == "mix-2"


@responses_lib.activate
def test_get_user_mixes_empty_page():
    """get_user_mixes() returns empty list when no items in page"""
    responses_lib.add(responses_lib.GET, MIXES_PAGE_URL, json={"rows": []}, status=200)
    _, endpoint = _make_session()
    result = endpoint.get_user_mixes()
    assert result == []


@responses_lib.activate
def test_get_mix_tracks_returns_tracks():
    """get_mix_tracks() returns list of track dicts from second row"""
    responses_lib.add(responses_lib.GET, MIX_PAGE_URL, json=_mix_tracks_response(), status=200)
    _, endpoint = _make_session()
    result = endpoint.get_mix_tracks("mix-1")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == 101
    assert result[0]["title"] == "Track One"


@responses_lib.activate
def test_get_mix_tracks_empty_when_no_track_rows():
    """get_mix_tracks() returns empty list when only metadata row present"""
    single_row_response = {"rows": [{"modules": [{"type": "MIX_HEADER"}]}]}
    responses_lib.add(responses_lib.GET, MIX_PAGE_URL, json=single_row_response, status=200)
    _, endpoint = _make_session()
    result = endpoint.get_mix_tracks("mix-1")
    assert result == []


@responses_lib.activate
def test_get_mix_tracks_raises_not_found_on_404():
    """get_mix_tracks() raises NotFoundError on 404"""
    responses_lib.add(responses_lib.GET, MIX_PAGE_URL, status=404, json={"error": "not found"})
    _, endpoint = _make_session()
    with pytest.raises(NotFoundError):
        endpoint.get_mix_tracks("bad-mix-id")


def test_session_mixes_property_returns_endpoint():
    """session.mixes should return MixesEndpoint instance"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    assert isinstance(session.mixes, MixesEndpoint)


def test_session_mixes_property_caches_instance():
    """session.mixes should return same instance on repeated access"""
    config = Config(client_id="test", client_secret="test")
    session = TidalSession(config)
    assert session.mixes is session.mixes
