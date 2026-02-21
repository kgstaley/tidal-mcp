"""Artists endpoint - TIDAL API wrapper for artist operations"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_client.session import TidalSession

ALBUM_FILTERS = {"albums": "ALBUMS", "ep_singles": "EPSSINGLES", "other": "OTHER"}


class ArtistsEndpoint:
    """Handle all artist-related API operations"""

    def __init__(self, session: "TidalSession"):
        """Initialize endpoint with session

        Args:
            session: TidalSession instance for making API requests
        """
        self.session = session

    def get(self, artist_id: str) -> dict:
        """Get artist by ID"""
        return self.session.request("GET", f"artists/{artist_id}")

    def get_bio(self, artist_id: str) -> str | None:
        """Get artist biography text.

        Returns:
            Biography text string, or None if not available.
        """
        result = self.session.request("GET", f"artists/{artist_id}/bio")
        return result.get("text")

    def get_top_tracks(self, artist_id: str, limit: int = 20) -> list[dict]:
        """Get artist's top tracks.

        Args:
            limit: Maximum number of tracks to return (default 20)
        """
        result = self.session.request("GET", f"artists/{artist_id}/toptracks", params={"limit": limit})
        return result.get("items", [])

    def get_albums(self, artist_id: str, filter: str = "albums", limit: int = 50, offset: int = 0) -> list[dict]:
        """Get artist's albums.

        Args:
            filter: One of "albums", "ep_singles", "other"
            limit: Maximum results
            offset: Pagination offset
        """
        api_filter = ALBUM_FILTERS.get(filter, "ALBUMS")
        result = self.session.request(
            "GET",
            f"artists/{artist_id}/albums",
            params={"filter": api_filter, "limit": limit, "offset": offset},
        )
        return result.get("items", [])

    def get_similar(self, artist_id: str) -> list[dict]:
        """Get artists similar to the given artist."""
        result = self.session.request("GET", f"artists/{artist_id}/similar")
        return result.get("items", [])

    def get_radio(self, artist_id: str, limit: int = 100) -> list[dict]:
        """Get radio tracks based on the given artist.

        Args:
            limit: Maximum tracks (max 100, TIDAL hardcodes this server-side)
        """
        result = self.session.request("GET", f"artists/{artist_id}/radio", params={"limit": limit})
        return result.get("items", [])
