"""Core TIDAL API session management"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from tidal_client.config import Config
from tidal_client.exceptions import (
    NotFoundError,
    RateLimitError,
    TidalAPIError,
)

if TYPE_CHECKING:
    from tidal_client.endpoints.albums import AlbumsEndpoint
    from tidal_client.endpoints.artists import ArtistsEndpoint
    from tidal_client.endpoints.tracks import TracksEndpoint


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

        # Lazy-loaded endpoints
        self._albums: AlbumsEndpoint | None = None
        self._artists: ArtistsEndpoint | None = None
        self._tracks: TracksEndpoint | None = None

    def _is_token_valid(self) -> bool:
        """Check if current access token is valid and not expired"""
        if not self._access_token:
            return False

        if not self._token_expires_at:
            return False

        # Consider token invalid if expiring within 60 seconds
        return datetime.now() < (self._token_expires_at - timedelta(seconds=60))

    def request_device_code(self) -> dict:
        """Request device code for OAuth Device Code Flow

        This is step 1 of the OAuth Device Code Flow. The returned user_code
        should be displayed to the user, who then visits verification_uri to
        authorize the application.

        Returns:
            Dict containing:
            - device_code: Code for polling token endpoint
            - user_code: Code for user to enter at verification URL
            - verification_uri: URL where user authorizes the app
            - verification_uri_complete: URL with user_code pre-filled
            - expires_in: Seconds until device_code expires
            - interval: Recommended polling interval in seconds

        Raises:
            TidalAPIError: If device code request fails
        """
        url = self.config.device_auth_url

        # OAuth requires application/x-www-form-urlencoded
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Standard OAuth scope for TIDAL: read user, write user, write subscription
        data = {
            "client_id": self.config.client_id,
            "scope": "r_usr w_usr w_sub",
        }

        try:
            response = self.http.post(url, headers=headers, data=data, timeout=self.config.default_timeout)
            response.raise_for_status()
            return response.json()

        except HTTPError as e:
            error_text = e.response.text[:200] if e.response.text else "No details"
            raise TidalAPIError(f"Device code request failed (HTTP {e.response.status_code}): {error_text}")

        except Timeout:
            raise TidalAPIError(f"Device code request timeout after {self.config.default_timeout}s")

        except ConnectionError as e:
            error_msg = str(e)[:200] if str(e) else "Connection failed"
            raise TidalAPIError(f"Device code request connection error: {error_msg}")

        except RequestsJSONDecodeError:
            raise TidalAPIError("Invalid JSON response from auth server")

    def poll_for_token(self, device_code: str, interval: int = 5, timeout: int = 300) -> dict:
        """Poll for OAuth token after user authorization

        This is step 2 of the OAuth Device Code Flow. Polls the token endpoint
        until the user authorizes the app, denies access, or the request times out.

        Args:
            device_code: Device code from request_device_code()
            interval: Seconds to wait between polling attempts (default: 5)
            timeout: Maximum seconds to poll before giving up (default: 300)

        Returns:
            Token response dict with access_token, refresh_token, expires_in, user

        Raises:
            TidalAPIError: If user denies, code expires, or polling times out
        """
        url = self.config.auth_token_url

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                raise TidalAPIError(f"OAuth polling timeout after {timeout}s")

            try:
                response = self.http.post(url, headers=headers, data=data, timeout=self.config.default_timeout)
                response.raise_for_status()

                # Success - extract tokens and user info
                token_data = response.json()

                self._access_token = token_data["access_token"]
                self._refresh_token = token_data.get("refresh_token")

                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                user_data = token_data.get("user", {})
                self._user_id = user_data.get("user_id")

                return token_data

            except HTTPError as e:
                # Parse error response
                try:
                    error_data = e.response.json()
                    error_code = error_data.get("error", "unknown")
                except Exception:
                    error_code = "unknown"

                # Check if we should retry or fail
                if error_code == "authorization_pending":
                    # User hasn't authorized yet - wait and retry
                    time.sleep(interval)
                    continue
                elif error_code == "slow_down":
                    # Polling too fast - increase interval and retry
                    time.sleep(interval + 5)
                    continue
                else:
                    # Terminal error (access_denied, expired_token, etc.)
                    error_text = e.response.text[:200] if e.response.text else error_code
                    raise TidalAPIError(f"OAuth authorization failed: {error_text}")

            except (Timeout, ConnectionError):
                # Network error - wait and retry
                time.sleep(interval)
                continue

            except RequestsJSONDecodeError:
                # Invalid response - wait and retry
                time.sleep(interval)
                continue

    def refresh_access_token(self) -> dict:
        """Refresh expired access token using refresh token

        Uses the refresh token to obtain a new access token without requiring
        the user to re-authorize. Should be called when access token expires.

        Returns:
            Token response dict with new access_token, refresh_token, expires_in

        Raises:
            TidalAPIError: If no refresh token or refresh fails
        """
        if not self._refresh_token:
            raise TidalAPIError("No refresh token available. Please re-authenticate.")

        url = self.config.auth_token_url

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            response = self.http.post(url, headers=headers, data=data, timeout=self.config.default_timeout)
            response.raise_for_status()

            # Success - extract tokens and update session
            token_data = response.json()

            self._access_token = token_data["access_token"]

            # Refresh token may be rotated (new refresh token returned)
            if "refresh_token" in token_data:
                self._refresh_token = token_data["refresh_token"]

            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Update user_id if present
            user_data = token_data.get("user", {})
            if "user_id" in user_data:
                self._user_id = user_data["user_id"]

            return token_data

        except HTTPError as e:
            error_text = e.response.text[:200] if e.response.text else "Unknown error"
            raise TidalAPIError(f"Token refresh failed: {error_text}")

        except Timeout:
            raise TidalAPIError(f"Token refresh timeout after {self.config.default_timeout}s")

        except ConnectionError as e:
            error_msg = str(e)[:200] if str(e) else "Connection failed"
            raise TidalAPIError(f"Token refresh connection error: {error_msg}")

        except RequestsJSONDecodeError:
            raise TidalAPIError("Invalid JSON response from token refresh")

    def request(self, method: str, path: str, **kwargs) -> dict:
        """Make HTTP request to TIDAL API with automatic token refresh

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path relative to api_v1_url (e.g., "artists/123")
            **kwargs: Additional arguments passed to requests.request()

        Returns:
            Parsed JSON response as dict

        Raises:
            NotFoundError: Resource not found (404)
            RateLimitError: Rate limit exceeded (429)
            TidalAPIError: Network errors, timeouts, or other HTTP errors
        """
        # Auto-refresh expired token before making request
        if not self._is_token_valid() and self._refresh_token:
            self.refresh_access_token()

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

        except HTTPError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            else:
                # Limit error text to avoid leaking sensitive info
                error_text = e.response.text[:200] if e.response.text else "No details"
                raise TidalAPIError(f"HTTP {e.response.status_code}: {error_text}")

        except Timeout:
            raise TidalAPIError(f"Request timeout after {timeout}s: {path}")

        except ConnectionError as e:
            # Truncate to prevent info leakage similar to HTTP errors
            error_msg = str(e)[:200] if str(e) else "Connection failed"
            raise TidalAPIError(f"Connection error: {error_msg}")

        except RequestsJSONDecodeError:
            raise TidalAPIError(f"Invalid JSON response from API: {path}")

    def save_session(self, filepath: str) -> None:
        """Save session state to JSON file

        Args:
            filepath: Absolute path to save session file

        Raises:
            TidalAPIError: If file cannot be written
        """
        session_data = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "user_id": self._user_id,
            "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
        }

        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(session_data, f, indent=2)

            # Restrict permissions to owner only (rw-------)
            os.chmod(filepath, 0o600)

        except OSError as e:
            raise TidalAPIError(f"Failed to save session file: {str(e)[:200]}")

    def load_session(self, filepath: str) -> None:
        """Load session state from JSON file

        Args:
            filepath: Absolute path to session file
        """
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath) as f:
                session_data = json.load(f)
        except json.JSONDecodeError:
            # Invalid JSON - treat as missing session
            return
        except OSError:
            # Permission denied or other I/O error - treat as missing session
            return

        self._access_token = session_data.get("access_token")
        self._refresh_token = session_data.get("refresh_token")
        self._user_id = session_data.get("user_id")

        expires_at_str = session_data.get("expires_at")
        if expires_at_str:
            self._token_expires_at = datetime.fromisoformat(expires_at_str)

    @property
    def albums(self) -> "AlbumsEndpoint":
        """Lazy-load albums endpoint

        Returns:
            AlbumsEndpoint instance for album operations
        """
        if not self._albums:
            from tidal_client.endpoints.albums import AlbumsEndpoint

            self._albums = AlbumsEndpoint(self)
        return self._albums

    @property
    def artists(self) -> "ArtistsEndpoint":
        """Lazy-load artists endpoint

        Returns:
            ArtistsEndpoint instance for artist operations
        """
        if not self._artists:
            from tidal_client.endpoints.artists import ArtistsEndpoint

            self._artists = ArtistsEndpoint(self)
        return self._artists

    @property
    def tracks(self) -> "TracksEndpoint":
        """Lazy-load tracks endpoint

        Returns:
            TracksEndpoint instance for track operations
        """
        if not self._tracks:
            from tidal_client.endpoints.tracks import TracksEndpoint

            self._tracks = TracksEndpoint(self)
        return self._tracks
