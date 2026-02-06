"""Authentication routes for TIDAL API."""

from flask import Blueprint, jsonify

from tidal_api.browser_session import BrowserSession
from tidal_api.utils import SESSION_FILE

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["GET"])
def login():
    """
    Initiates the TIDAL authentication process.
    Automatically opens a browser for the user to login to their TIDAL account.
    """
    session = BrowserSession()

    def log_message(msg):
        print(f"TIDAL AUTH: {msg}")

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
