"""Core TIDAL API session management"""

from datetime import datetime, timedelta

import requests

from tidal_client.config import Config
from tidal_client.exceptions import (
    NotFoundError,
    RateLimitError,
    TidalAPIError,
)


class TidalSession:
    """Manages TIDAL API HTTP session with OAuth token lifecycle"""

    def __init__(self, config: Config):
        self.config = config
        self.http = requests.Session()

        # OAuth token state
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._user_id: str | None = None

    def _is_token_valid(self) -> bool:
        """Check if current access token is valid and not expired"""
        if not self._access_token:
            return False

        if not self._token_expires_at:
            return False

        # Consider token invalid if expiring within 60 seconds
        return datetime.now() < (self._token_expires_at - timedelta(seconds=60))

    def request(self, method: str, path: str, **kwargs) -> dict:
        """Make HTTP request to TIDAL API with error handling

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path relative to api_v1_url (e.g., "artists/123")
            **kwargs: Additional arguments passed to requests.request()

        Returns:
            Parsed JSON response as dict

        Raises:
            NotFoundError: Resource not found (404)
            RateLimitError: Rate limit exceeded (429)
            TidalAPIError: Other HTTP errors
        """
        url = self.config.api_v1_url + path

        # Add auth header if token available
        headers = kwargs.pop("headers", {})
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        # Set default timeout
        timeout = kwargs.pop("timeout", self.config.default_timeout)

        try:
            response = self.http.request(method=method, url=url, headers=headers, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            else:
                raise TidalAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
