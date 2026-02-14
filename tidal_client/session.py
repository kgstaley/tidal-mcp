# tidal_client/session.py
"""Core TIDAL API session management"""
import json
import logging
import os
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import requests

from tidal_client.config import Config
from tidal_client.exceptions import (
    TidalAPIError,
    NotFoundError,
    RateLimitError,
)

# HTTP status code constants
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429

# Session file formatting
SESSION_FILE_INDENT = 2


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
            response = self.http.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            # Guard against missing response object
            if e.response is None:
                raise TidalAPIError("HTTP error with no response") from e

            status_code = e.response.status_code

            if status_code == HTTP_NOT_FOUND:
                raise NotFoundError(f"Resource not found: {path}") from e
            elif status_code == HTTP_RATE_LIMIT:
                raise RateLimitError("Rate limit exceeded") from e
            else:
                # Truncate error body to prevent huge error messages
                error_body = e.response.text[:200] if e.response.text else "No response body"
                raise TidalAPIError(f"HTTP {status_code}: {error_body}") from e

    def save_session(self, session_file: str) -> None:
        """Save session tokens to file

        Args:
            session_file: Path to save session data (JSON format)

        Raises:
            OSError: If file cannot be written
        """
        session_data = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "user_id": self._user_id
        }

        try:
            Path(session_file).parent.mkdir(parents=True, exist_ok=True)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=SESSION_FILE_INDENT)
            # Set restrictive permissions (owner read/write only)
            os.chmod(session_file, 0o600)
        except OSError as e:
            logging.error(f"Failed to save session to {session_file}: {e}", exc_info=True)
            raise

    def load_session(self, session_file: str) -> None:
        """Load session tokens from file

        Args:
            session_file: Path to load session data from (JSON format)
        """
        if not Path(session_file).exists():
            return

        try:
            with open(session_file, encoding="utf-8") as f:
                session_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load session from {session_file}: {e}")
            return

        self._access_token = session_data.get("access_token")
        self._refresh_token = session_data.get("refresh_token")

        token_expires_str = session_data.get("token_expires_at")
        if token_expires_str:
            try:
                self._token_expires_at = datetime.fromisoformat(token_expires_str)
            except ValueError as e:
                logging.warning(f"Invalid datetime format in session file: {e}")
                self._token_expires_at = None

        self._user_id = session_data.get("user_id")
