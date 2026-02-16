"""Artists endpoint - TIDAL API wrapper for artist operations"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_client.session import TidalSession


class ArtistsEndpoint:
    """Handle all artist-related API operations"""

    def __init__(self, session: 'TidalSession'):
        """Initialize endpoint with session

        Args:
            session: TidalSession instance for making API requests
        """
        self.session = session

    def get(self, artist_id: str) -> dict:
        """Get artist by ID

        Args:
            artist_id: TIDAL artist ID

        Returns:
            Artist dict with id, name, picture, popularity, etc.

        Raises:
            NotFoundError: If artist doesn't exist
            TidalAPIError: If request fails
        """
        return self.session.request("GET", f"artists/{artist_id}")
