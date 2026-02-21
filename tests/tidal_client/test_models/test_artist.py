"""Tests for Artist TypedDict model"""

from typing import get_type_hints

from tidal_client.models.artist import ArtistDict


def test_artist_dict_has_required_fields():
    """ArtistDict should define required fields"""
    # TypedDict with total=False makes all fields optional,
    # but we can verify they're defined in the type hints
    hints = get_type_hints(ArtistDict)

    # Core fields that TIDAL API returns
    assert "id" in hints
    assert "name" in hints
    assert "picture" in hints


def test_artist_dict_structure():
    """ArtistDict should accept valid artist data"""
    # Create a sample artist dict matching TIDAL API response
    artist: ArtistDict = {
        "id": "12345",
        "name": "Test Artist",
        "picture": "artist-picture-uuid",
        "popularity": 85,
        "url": "https://tidal.com/artist/12345",
    }

    # Verify it's a valid dict
    assert isinstance(artist, dict)
    assert artist["id"] == "12345"
    assert artist["name"] == "Test Artist"


def test_artist_dict_allows_optional_fields():
    """ArtistDict should work with minimal fields"""
    # Should work with just id and name
    artist: ArtistDict = {"id": "67890", "name": "Minimal Artist"}

    assert artist["id"] == "67890"
    assert artist["name"] == "Minimal Artist"
