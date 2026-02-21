"""Tracks endpoint - TIDAL API wrapper for track operations"""

from typing import TYPE_CHECKING

from tidal_client.exceptions import NotFoundError

if TYPE_CHECKING:
    from tidal_client.session import TidalSession


class TracksEndpoint:
    """Handle all track-related API operations"""

    def __init__(self, session: "TidalSession"):
        """Initialize endpoint with session

        Args:
            session: TidalSession instance for making API requests
        """
        self.session = session

    def get(self, track_id: str) -> dict:
        """Get track by ID"""
        return self.session.request("GET", f"tracks/{track_id}")

    def get_lyrics(self, track_id: str) -> dict | None:
        """Get lyrics for a track.

        Args:
            track_id: TIDAL track ID

        Returns:
            Dict with text, subtitles, and provider keys, or None if unavailable.
        """
        try:
            result = self.session.request("GET", f"tracks/{track_id}/lyrics")
        except NotFoundError:
            return None

        text = result.get("text")
        if text is None:
            return None

        return {
            "text": text,
            "subtitles": result.get("subtitles"),
            "provider": result.get("provider"),
        }

    def get_recommendations(self, track_id: str, limit: int = 10) -> list[dict]:
        """Get track recommendations based on a given track.

        Args:
            track_id: TIDAL track ID
            limit: Maximum number of recommendations to return (default 10)

        Returns:
            List of recommended track dicts, or empty list if track not found.
        """
        try:
            result = self.session.request(
                "GET",
                f"tracks/{track_id}/recommendations",
                params={"limit": limit},
            )
        except NotFoundError:
            return []
        return result.get("items", [])
