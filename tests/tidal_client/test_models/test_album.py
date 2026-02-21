"""Tests for Album TypedDict model"""

from typing import get_type_hints

from tidal_client.models.album import AlbumDict


def test_album_dict_has_required_fields():
    """AlbumDict should define core identification and media fields"""
    hints = get_type_hints(AlbumDict)

    # Core fields that TIDAL API returns
    assert "id" in hints
    assert "title" in hints
    assert "cover" in hints


def test_album_dict_has_metadata_fields():
    """AlbumDict should define metadata fields"""
    hints = get_type_hints(AlbumDict)

    assert "releaseDate" in hints
    assert "numberOfTracks" in hints
    assert "duration" in hints
    assert "explicit" in hints
    assert "popularity" in hints


def test_album_dict_has_relationship_fields():
    """AlbumDict should define artist relationship fields"""
    hints = get_type_hints(AlbumDict)

    assert "artist" in hints
    assert "artists" in hints


def test_album_dict_structure():
    """AlbumDict should accept valid album data matching TIDAL API response"""
    album: AlbumDict = {
        "id": "12345",
        "title": "Test Album",
        "artist": {"id": "67890", "name": "Test Artist"},
        "artists": [{"id": "67890", "name": "Test Artist"}],
        "cover": "album-picture-uuid",
        "releaseDate": "2024-01-15",
        "numberOfTracks": 12,
        "duration": 2880,
        "explicit": False,
        "popularity": 72,
    }

    assert isinstance(album, dict)
    assert album["id"] == "12345"
    assert album["title"] == "Test Album"
    assert album["numberOfTracks"] == 12


def test_album_dict_allows_optional_fields():
    """AlbumDict should work with minimal fields (total=False)"""
    album: AlbumDict = {
        "id": "99999",
        "title": "Minimal Album",
    }

    assert album["id"] == "99999"
    assert album["title"] == "Minimal Album"


def test_album_dict_allows_none_values():
    """AlbumDict should accept None for optional nullable fields"""
    album: AlbumDict = {
        "id": "11111",
        "title": "Album With Nulls",
        "artist": None,
        "artists": None,
        "cover": None,
        "releaseDate": None,
    }

    assert album["artist"] is None
    assert album["cover"] is None
