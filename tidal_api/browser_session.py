import logging
import os
import webbrowser
from collections.abc import Callable
from pathlib import Path

import tidalapi

logger = logging.getLogger(__name__)


class BrowserSession(tidalapi.Session):
    """
    Extended tidalapi.Session that automatically opens the login URL in a browser.

    Reads optional env vars to override tidalapi's built-in OAuth credentials:
      TIDAL_CLIENT_ID      — OAuth client ID
      TIDAL_CLIENT_SECRET   — OAuth client secret
    """

    def __init__(self, config: tidalapi.Config | None = None) -> None:
        if config is None:
            config = tidalapi.Config()

        client_id = os.environ.get("TIDAL_CLIENT_ID")
        client_secret = os.environ.get("TIDAL_CLIENT_SECRET")

        if client_id:
            config.client_id = client_id
            logger.info("Using custom TIDAL_CLIENT_ID from environment")
        if client_secret:
            config.client_secret = client_secret

        super().__init__(config)

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
