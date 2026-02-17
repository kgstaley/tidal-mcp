"""Authentication routes for TIDAL API."""

import logging

from flask import Blueprint, jsonify

from tidal_api.utils import SESSION_FILE, _create_tidal_session

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["GET"])
def login():
    """
    Initiates the TIDAL authentication process.
    Uses BrowserSession (tidalapi) for browser-based OAuth login.
    """
    from tidal_api.browser_session import BrowserSession

    session = BrowserSession()

    def log_message(msg):
        logger.info("TIDAL AUTH: %s", msg)

    try:
        login_success = session.login_session_file_auto(SESSION_FILE, fn_print=log_message)

        if login_success:
            return jsonify(
                {"status": "success", "message": "Successfully authenticated with TIDAL", "user_id": session.user.id}
            )
        else:
            return jsonify({"status": "error", "message": "Authentication failed"}), 401

    except TimeoutError:
        return jsonify({"status": "error", "message": "Authentication timed out"}), 408

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/api/auth/status", methods=["GET"])
def auth_status():
    """
    Check if there's an active authenticated session.
    Supports both BrowserSession (tidalapi) and TidalSession (custom client).
    """
    if not SESSION_FILE.exists():
        return jsonify({"authenticated": False, "message": "No session file found"})

    session = _create_tidal_session()

    # Duck-type: BrowserSession has login_session_file_auto; TidalSession does not
    if hasattr(session, "login_session_file_auto"):
        login_success = session.login_session_file_auto(SESSION_FILE)
        if not login_success:
            return jsonify({"authenticated": False, "message": "Invalid or expired session"})

        user_info = {
            "id": session.user.id,
            "username": session.user.username if hasattr(session.user, "username") else "N/A",
            "email": session.user.email if hasattr(session.user, "email") else "N/A",
        }
        return jsonify({"authenticated": True, "message": "Valid TIDAL session", "user": user_info})
    else:
        # Custom client: session loaded in _create_tidal_session(), check token validity
        if not session._is_token_valid():
            return jsonify({"authenticated": False, "message": "Invalid or expired session"})

        user_info = {"id": session._user_id}
        return jsonify({"authenticated": True, "message": "Valid TIDAL session", "user": user_info})
