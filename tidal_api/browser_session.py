import logging
import os
import secrets
import webbrowser
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlencode

import tidalapi

logger = logging.getLogger(__name__)

DEFAULT_FLASK_PORT = 5050


class BrowserSession(tidalapi.Session):
    """
    Extended tidalapi.Session that automatically opens the login URL in a browser.

    Reads optional env vars to override tidalapi's built-in OAuth credentials:
      TIDAL_CLIENT_ID      — OAuth client ID
      TIDAL_CLIENT_SECRET   — OAuth client secret
      TIDAL_REDIRECT_URI    — PKCE redirect URI (default: http://localhost:{port}/api/auth/callback)
    """

    def __init__(self, config: tidalapi.Config | None = None) -> None:
        if config is None:
            config = tidalapi.Config()

        client_id = os.environ.get("TIDAL_CLIENT_ID")
        client_secret = os.environ.get("TIDAL_CLIENT_SECRET")

        if client_id:
            config.client_id = client_id
            config.client_id_pkce = client_id
            logger.info("Using custom TIDAL_CLIENT_ID from environment")
        if client_secret:
            config.client_secret = client_secret
            config.client_secret_pkce = client_secret

        if client_id:
            flask_port = int(os.environ.get("TIDAL_MCP_PORT", DEFAULT_FLASK_PORT))
            default_redirect = f"http://localhost:{flask_port}/api/auth/callback"
            config.pkce_uri_redirect = os.environ.get("TIDAL_REDIRECT_URI", default_redirect)

        super().__init__(config)

    @property
    def uses_custom_credentials(self) -> bool:
        """Check if custom TIDAL developer credentials are configured."""
        return bool(os.environ.get("TIDAL_CLIENT_ID"))

    def get_pkce_login_url(self) -> tuple[str, str]:
        """Get the PKCE authorization URL with a CSRF state parameter.

        Returns:
            Tuple of (authorization_url, state) where state must be validated on callback.
        """
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "redirect_uri": self.config.pkce_uri_redirect,
            "client_id": self.config.client_id_pkce,
            "lang": "EN",
            "appMode": "android",
            "client_unique_key": self.config.client_unique_key,
            "code_challenge": self.config.code_challenge,
            "code_challenge_method": "S256",
            "restrict_signup": "true",
            "state": state,
        }
        url = self.config.api_pkce_auth + "?" + urlencode(params)
        return url, state

    def complete_pkce_login(self, code: str) -> tuple[bool, str]:
        """Complete the PKCE login flow using the authorization code from the callback.

        Delegates to tidalapi's pkce_get_auth_token + process_auth_token.
        Constructs a synthetic https:// URL to satisfy tidalapi's URL scheme check
        (it only parses the ``code`` query param from the URL).

        Args:
            code: The authorization code from TIDAL's redirect

        Returns:
            Tuple of (success: bool, error_detail: str). error_detail is empty on success.
        """
        try:
            # tidalapi's pkce_get_auth_token rejects http:// URLs (checks for "https://").
            # We already have the code from Flask, so build a synthetic URL it can parse.
            synthetic_url = f"https://localhost/callback?code={code}"
            token_json = self.pkce_get_auth_token(synthetic_url)
            self.process_auth_token(token_json, is_pkce_token=True)
            if self.check_login():
                return True, ""
            return False, "Token received but session validation failed"
        except Exception as e:
            logger.error("PKCE login failed: %s", e, exc_info=True)
            return False, str(e)

    def login_oauth_simple(self, fn_print: Callable[[str], None] = print) -> None:
        """
        Login to TIDAL with a remote link, automatically opening the URL in a browser.

        :param fn_print: The function to display additional information
        :raises: TimeoutError: If the login takes too long
        """
        login, future = self.login_oauth()

        # Display information about the login
        text = "Opening browser for TIDAL login. The code will expire in {0} seconds"
        fn_print(text.format(login.expires_in))

        # Open the URL in the default browser
        auth_url = login.verification_uri_complete
        if not auth_url.startswith("http"):
            auth_url = "https://" + auth_url
        webbrowser.open(auth_url)

        # Wait for the authentication to complete
        future.result()

    def login_session_file_auto(
        self,
        session_file: Path,
        do_pkce: bool | None = False,
        fn_print: Callable[[str], None] = print,
    ) -> bool:
        """
        Logs in to the TIDAL api using an existing OAuth/PKCE session file,
        automatically opening the browser for authentication if needed.

        :param session_file: The session json file
        :param do_pkce: Perform PKCE login. Default: Use OAuth logon
        :param fn_print: A function to display information
        :return: Returns true if the login was successful
        """
        self.load_session_from_file(session_file)

        # Session could not be loaded, attempt to create a new session
        if not self.check_login():
            if do_pkce:
                fn_print("Creating new session (PKCE)...")
                self.login_pkce(fn_print=fn_print)
            else:
                fn_print("Creating new session (OAuth)...")
                self.login_oauth_simple(fn_print=fn_print)

        if self.check_login():
            fn_print(f"TIDAL Login OK, creds saved in {str(session_file)}")
            self.save_session_to_file(session_file)
            return True
        else:
            fn_print("TIDAL Login KO")
            return False
