"""Integration tests for TIDAL authentication flow with tidalapi patch.

These tests verify that the local patch to tidalapi (params → data) works correctly
by actually calling TIDAL's API endpoints.
"""

import pytest

from tidal_api.browser_session import BrowserSession


class TestDeviceAuthorizationIntegration:
    """Test device authorization flow with real TIDAL API calls."""

    def test_device_authorization_request_format(self):
        """
        Test that device authorization uses correct request format (form body, not query params).

        This is the core fix: tidalapi must use data= instead of params= to send
        credentials in the request body with Content-Type: application/x-www-form-urlencoded.
        """
        session = BrowserSession()

        # Call get_link_login which should POST to device_authorization endpoint
        # This will fail if the patch isn't applied (415 Unsupported Media Type)
        link_login = session.get_link_login()

        # If we got here, the request succeeded (patch is applied)
        assert link_login.device_code is not None
        assert link_login.user_code is not None
        assert link_login.verification_uri == "link.tidal.com"
        assert link_login.expires_in > 0
        assert link_login.interval >= 1

    def test_device_authorization_returns_valid_codes(self):
        """Test that device authorization returns valid device and user codes."""
        session = BrowserSession()
        link_login = session.get_link_login()

        # Validate response structure
        assert isinstance(link_login.device_code, str)
        assert len(link_login.device_code) > 0
        assert isinstance(link_login.user_code, str)
        assert len(link_login.user_code) > 0

        # User code should be alphanumeric and short (typically 5-6 chars)
        assert link_login.user_code.isalnum()
        assert 4 <= len(link_login.user_code) <= 8

    def test_verification_uri_format(self):
        """Test that verification URI is correctly formatted."""
        session = BrowserSession()
        link_login = session.get_link_login()

        assert link_login.verification_uri in ["link.tidal.com", "https://link.tidal.com"]
        assert link_login.verification_uri_complete.endswith(link_login.user_code)

    @pytest.mark.skip(reason="Requires manual interaction with TIDAL login page")
    def test_full_authentication_flow(self, tmp_path):
        """
        Full integration test requiring manual TIDAL login.

        Run with: pytest -v -k test_full_authentication_flow --run-live

        This test will:
        1. Get device code
        2. Print user code and URL
        3. Wait for manual login
        4. Verify session is authenticated
        """
        session = BrowserSession()
        session_file = tmp_path / "test-session.json"

        # Get link login (device code flow)
        link_login = session.get_link_login()

        print(f"\n{'=' * 60}")
        print("MANUAL TEST: Please complete TIDAL login")
        print(f"{'=' * 60}")
        print(f"1. Open: {link_login.verification_uri_complete}")
        print(f"2. Enter code: {link_login.user_code}")
        print("3. Press Enter here when done...")
        print(f"{'=' * 60}")
        input()

        # Process the link login (poll for token)
        success = session.process_link_login(link_login, until_expiry=True)
        assert success, "Authentication failed"

        # Verify session is valid
        assert session.check_login()
        assert session.user is not None
        assert session.user.id is not None

        # Save and reload session
        session.save_session_to_file(session_file)
        assert session_file.exists()

        # Verify session can be reloaded
        new_session = BrowserSession()
        new_session.load_session_from_file(session_file)
        assert new_session.check_login()
        assert new_session.user.id == session.user.id
