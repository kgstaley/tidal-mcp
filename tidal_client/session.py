"""Core TIDAL API session management"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

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
            TidalAPIError: Network errors, timeouts, or other HTTP errors
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
