"""Tests for Track TypedDict model"""
from typing import get_type_hints

from tidal_client.models.track import TrackDict


def test_track_dict_has_core_fields():
    """TrackDict should define core identification fields"""
    hints = get_type_hints(TrackDict)

    assert "id" in hints
    assert "title" in hints


def test_track_dict_has_metadata_fields():
    """TrackDict should define track metadata fields"""
    hints = get_type_hints(TrackDict)

    assert "duration" in hints
    assert "trackNumber" in hints
    assert "volumeNumber" in hints
    assert "explicit" in hints
    assert "isrc" in hints
    assert "popularity" in hints
    assert "audioQuality" in hints


def test_track_dict_has_relationship_fields():
    """TrackDict should define artist and album relationship fields"""
    hints = get_type_hints(TrackDict)

    assert "artist" in hints
    assert "artists" in hints
    assert "album" in hints


def test_track_dict_structure():
    """TrackDict should accept valid track data matching TIDAL API response"""
    track: TrackDict = {
        "id": "12345",
        "title": "Test Track",
        "artist": {"id": "67890", "name": "Test Artist"},
        "artists": [{"id": "67890", "name": "Test Artist"}],
        "album": {"id": "99999", "title": "Test Album"},
        "duration": 240,
        "trackNumber": 3,
        "volumeNumber": 1,
        "explicit": False,
        "isrc": "USAT12345678",
        "popularity": 72,
        "audioQuality": "LOSSLESS",
    }

    assert isinstance(track, dict)
    assert track["id"] == "12345"
    assert track["title"] == "Test Track"
    assert track["duration"] == 240
    assert track["trackNumber"] == 3


def test_track_dict_allows_optional_fields():
    """TrackDict should work with minimal fields (total=False)"""
    track: TrackDict = {
        "id": "99999",
        "title": "Minimal Track",
    }

    assert track["id"] == "99999"
    assert track["title"] == "Minimal Track"


def test_track_dict_allows_none_values():
    """TrackDict should accept None for optional nullable fields"""
    track: TrackDict = {
        "id": "11111",
        "title": "Track With Nulls",
        "artist": None,
        "artists": None,
        "album": None,
        "duration": None,
        "isrc": None,
    }

    assert track["artist"] is None
    assert track["album"] is None
    assert track["duration"] is None
