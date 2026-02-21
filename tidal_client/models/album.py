"""Album entity TypedDict definitions"""

from typing import TypedDict


class AlbumDict(TypedDict, total=False):
    """Album entity from TIDAL API

    All fields are optional to match TIDAL API response flexibility.
    Different endpoints return different subsets of fields.
    """

    # Core identification
    id: str
    title: str

    # Relationships
    artist: dict | None
    artists: list[dict] | None

    # Media
    cover: str | None  # UUID for album cover art

    # Release metadata
    releaseDate: str | None

    # Track and duration info
    numberOfTracks: int | None
    duration: int | None

    # Content flags and metrics
    explicit: bool | None
    popularity: int | None
