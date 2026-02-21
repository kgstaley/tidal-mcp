"""Mix entity TypedDict definitions"""

from typing import TypedDict


class MixDict(TypedDict, total=False):
    """Mix entity from TIDAL API

    All fields are optional to match TIDAL API response flexibility.
    Different endpoints return different subsets of fields.
    """

    id: str
    title: str | None
    subTitle: str | None
    shortSubtitle: str | None
    mixType: str | None
    images: dict | None
