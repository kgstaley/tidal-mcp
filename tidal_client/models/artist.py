"""Artist entity TypedDict definitions"""

from typing import TypedDict


class ArtistDict(TypedDict, total=False):
    """Artist entity from TIDAL API

    All fields are optional to match TIDAL API response flexibility.
    Different endpoints return different subsets of fields.
    """

    # Core identification
    id: str
    name: str

    # Media
    picture: str | None  # UUID for artist picture

    # Metadata
    url: str | None
    popularity: int | None

    # Biography
    bio: str | None

    # Relationships (artist roles)
    roles: list[str] | None
