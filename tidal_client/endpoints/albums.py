"""Albums endpoint - TIDAL API wrapper for album operations"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_client.session import TidalSession


class AlbumsEndpoint:
    """Handle all album-related API operations"""

    def __init__(self, session: "TidalSession"):
        """Initialize endpoint with session

        Args:
            session: TidalSession instance for making API requests
        """
        self.session = session

    def get(self, album_id: str) -> dict:
        """Get album by ID"""
        return self.session.request("GET", f"albums/{album_id}")

    def get_tracks(self, album_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get tracks from an album.

        Args:
            album_id: TIDAL album ID
            limit: Maximum number of tracks to return (default 50)
            offset: Pagination offset (default 0)

        Returns:
            List of track dicts from the album.
        """
        result = self.session.request(
            "GET",
            f"albums/{album_id}/tracks",
            params={"limit": limit, "offset": offset},
        )
        return result.get("items", [])

    def get_similar(self, album_id: str) -> list[dict]:
        """Get albums similar to the given album.

        Args:
            album_id: TIDAL album ID

        Returns:
            List of similar album dicts.
        """
        result = self.session.request("GET", f"albums/{album_id}/similar")
        return result.get("items", [])

    def get_review(self, album_id: str) -> str | None:
        """Get the editorial review for an album.

        Args:
            album_id: TIDAL album ID

        Returns:
            Review text string, or None if not available.
        """
        result = self.session.request("GET", f"albums/{album_id}/review")
        return result.get("text")
