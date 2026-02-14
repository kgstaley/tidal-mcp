# tidal_client/session.py
"""Core TIDAL API session management"""
from typing import Optional
from datetime import datetime, timedelta
import requests

from tidal_client.config import Config


class TidalSession:
    """Manages TIDAL API HTTP session with OAuth token lifecycle"""

    def __init__(self, config: Config):
        self.config = config
        self.http = requests.Session()

        # OAuth token state
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._user_id: Optional[str] = None

    def _is_token_valid(self) -> bool:
        """Check if current access token is valid and not expired"""
        if not self._access_token:
            return False

        if not self._token_expires_at:
            return False

        # Consider token invalid if expiring within 60 seconds
        return datetime.now() < (self._token_expires_at - timedelta(seconds=60))
