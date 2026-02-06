"""Authentication routes for TIDAL API."""

import logging
import threading
import webbrowser

from flask import Blueprint, jsonify, make_response, request

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import SESSION_FILE

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

# PKCE login coordination: tracks whether a PKCE callback has completed.
# The callback endpoint sets this to True; the MCP tool polls /api/auth/status
# to detect when auth is done (session file exists + valid).
_pkce_login_lock = threading.Lock()
_pkce_pending = False


def _set_pkce_pending(value: bool) -> None:
    global _pkce_pending
    with _pkce_login_lock:
        _pkce_pending = value


def _is_pkce_pending() -> bool:
    with _pkce_login_lock:
        return _pkce_pending


@auth_bp.route("/api/auth/login", methods=["GET"])
def login():
    """
    Initiates the TIDAL authentication process.

    If custom credentials (TIDAL_CLIENT_ID) are set, uses PKCE flow:
    opens browser, returns pending status. The MCP tool then polls /api/auth/status.

    Otherwise, uses the existing device code flow (blocking).
    """
    session = BrowserSession()

    # If session file already exists and is valid, return immediately
    if SESSION_FILE.exists():
        try:
            session.load_session_from_file(SESSION_FILE)
            if session.check_login():
                return jsonify(
                    {
                        "status": "success",
                        "message": "Successfully authenticated with TIDAL",
                        "user_id": session.user.id,
                    }
                )
        except Exception:
            logger.debug("Existing session file invalid, proceeding with fresh login")

    try:
        if session.uses_custom_credentials:
            # PKCE flow: open browser, return pending
            pkce_url = session.get_pkce_login_url()
            webbrowser.open(pkce_url)
            _set_pkce_pending(True)
            return jsonify(
                {
                    "status": "pending",
                    "message": "Browser opened for TIDAL login. Waiting for authorization...",
                    "flow": "pkce",
                }
            )
        else:
            # Device code flow (existing behavior, blocking)
            def log_message(msg):
                logger.info("TIDAL AUTH: %s", msg)

            login_success = session.login_session_file_auto(SESSION_FILE, fn_print=log_message)

            if login_success:
                return jsonify(
                    {
                        "status": "success",
                        "message": "Successfully authenticated with TIDAL",
                        "user_id": session.user.id,
                    }
                )
            else:
                return jsonify({"status": "error", "message": "Authentication failed"}), 401

    except TimeoutError:
        return jsonify({"status": "error", "message": "Authentication timed out"}), 408

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


_CALLBACK_SUCCESS_HTML = """<!DOCTYPE html>
<html><head><title>TIDAL Login</title></head>
<body style="font-family:system-ui,sans-serif;display:flex;justify-content:center;
align-items:center;height:100vh;margin:0">
<div style="text-align:center">
<h1>Login successful!</h1>
<p>You can close this tab and return to Claude.</p>
</div></body></html>"""

_CALLBACK_ERROR_HTML = """<!DOCTYPE html>
<html><head><title>TIDAL Login</title></head>
<body style="font-family:system-ui,sans-serif;display:flex;justify-content:center;
align-items:center;height:100vh;margin:0">
<div style="text-align:center">
<h1>Login failed</h1>
<p>{message}</p>
</div></body></html>"""


def _html_response(html: str, status: int = 200):
    resp = make_response(html, status)
    resp.headers["Content-Type"] = "text/html"
    return resp


@auth_bp.route("/api/auth/callback", methods=["GET"])
def callback():
    """
    PKCE callback endpoint. TIDAL redirects here with ?code=... after user login.
    Exchanges the code for tokens, saves the session, and returns a success page.
    """
    try:
        code = request.args.get("code")
        if not code:
            _set_pkce_pending(False)
            error_msg = request.args.get("error_description", request.args.get("error", "No authorization code"))
            logger.error("PKCE callback missing code: %s", error_msg)
            return _html_response(_CALLBACK_ERROR_HTML.format(message=error_msg), 400)

        session = BrowserSession()
        login_success = session.complete_pkce_login(code)

        if login_success:
            session.save_session_to_file(SESSION_FILE)
            logger.info("PKCE login successful, session saved")
            return _html_response(_CALLBACK_SUCCESS_HTML)
        else:
            logger.error("PKCE token exchange failed")
            return _html_response(_CALLBACK_ERROR_HTML.format(message="Token exchange failed. Please try again."), 401)
    except Exception as e:
        logger.error("PKCE callback error: %s", e, exc_info=True)
        return _html_response(_CALLBACK_ERROR_HTML.format(message="An unexpected error occurred."), 500)
    finally:
        _set_pkce_pending(False)


@auth_bp.route("/api/auth/status", methods=["GET"])
def auth_status():
    """
    Check if there's an active authenticated session.
    """
    if not SESSION_FILE.exists():
        return jsonify({"authenticated": False, "message": "No session file found"})

    session = BrowserSession()
    login_success = session.login_session_file_auto(SESSION_FILE)

    if login_success:
        user_info = {
            "id": session.user.id,
            "username": session.user.username if hasattr(session.user, "username") else "N/A",
            "email": session.user.email if hasattr(session.user, "email") else "N/A",
        }

        return jsonify({"authenticated": True, "message": "Valid TIDAL session", "user": user_info})
    else:
        return jsonify({"authenticated": False, "message": "Invalid or expired session"})
