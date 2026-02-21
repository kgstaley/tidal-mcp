"""API endpoint wrappers"""

from tidal_client.endpoints.albums import AlbumsEndpoint
from tidal_client.endpoints.artists import ArtistsEndpoint
from tidal_client.endpoints.mixes import MixesEndpoint
from tidal_client.endpoints.tracks import TracksEndpoint

__all__ = ["AlbumsEndpoint", "ArtistsEndpoint", "MixesEndpoint", "TracksEndpoint"]
