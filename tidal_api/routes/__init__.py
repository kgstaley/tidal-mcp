"""Flask route blueprints for the TIDAL API."""

from tidal_api.routes.albums import albums_bp
from tidal_api.routes.artists import artists_bp
from tidal_api.routes.auth import auth_bp
from tidal_api.routes.discovery import discovery_bp
from tidal_api.routes.favorites import favorites_bp
from tidal_api.routes.mixes import mixes_bp
from tidal_api.routes.playlists import playlists_bp
from tidal_api.routes.search import search_bp
from tidal_api.routes.tracks import tracks_bp

__all__ = [
    "albums_bp",
    "artists_bp",
    "auth_bp",
    "discovery_bp",
    "favorites_bp",
    "mixes_bp",
    "playlists_bp",
    "search_bp",
    "tracks_bp",
]
