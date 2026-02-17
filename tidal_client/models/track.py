"""Track entity TypedDict definitions"""
from typing import TypedDict


class TrackDict(TypedDict, total=False):
    """Track entity from TIDAL API

    All fields are optional to match TIDAL API response flexibility.
    Different endpoints return different subsets of fields.
    """
    # Core identification
    id: str
    title: str

    # Relationships
    artist: dict | None
    artists: list[dict] | None
    album: dict | None

    # Playback metadata
    duration: int | None
    trackNumber: int | None
    volumeNumber: int | None

    # Content flags and identifiers
    explicit: bool | None
    isrc: str | None

    # Metrics and quality
    popularity: int | None
    audioQuality: str | None


class LyricsDict(TypedDict, total=False):
    """Lyrics entity from TIDAL API lyrics endpoint"""
    text: str | None
    subtitles: str | None
    provider: str | None
