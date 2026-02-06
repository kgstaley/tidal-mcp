"""MCP server utilities: Flask lifecycle, validation, HTTP helpers."""

import logging
import os
import pathlib
import shutil
import subprocess

import requests

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_PORT = 5050
DEFAULT_TIMEOUT = 30
FLASK_PORT = int(os.environ.get("TIDAL_MCP_PORT", DEFAULT_PORT))
FLASK_APP_URL = f"http://127.0.0.1:{FLASK_PORT}"

# Path to Flask app
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
FLASK_APP_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "tidal_api", "app.py"))

# Shared HTTP session with connection pooling
http = requests.Session()
http.headers.update({"Content-Type": "application/json"})


def find_uv_executable() -> str:
    """Find the uv executable in the path or common locations."""
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    common_locations = [
        os.path.expanduser("~/.local/bin/uv"),
        os.path.expanduser("~/AppData/Local/Programs/Python/Python*/Scripts/uv.exe"),
        "/usr/local/bin/uv",
        "/opt/homebrew/bin/uv",
    ]

    for location in common_locations:
        if "*" in location:
            import glob

            matches = glob.glob(location)
            for match in matches:
                if os.path.isfile(match) and os.access(match, os.X_OK):
                    return match
        elif os.path.isfile(location) and os.access(location, os.X_OK):
            return location

    return "uv"


# Global variable to hold the Flask app process
flask_process = None


def start_flask_app() -> None:
    """Start the Flask app as a subprocess."""
    global flask_process

    logger.info("Starting TIDAL Flask app...")

    uv_executable = find_uv_executable()
    logger.info("Using uv executable: %s", uv_executable)

    flask_process = subprocess.Popen(
        [uv_executable, "run", "--with", "tidalapi", "--with", "flask", "--with", "requests", "python", FLASK_APP_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    logger.info("TIDAL Flask app started (pid=%s)", flask_process.pid)


def shutdown_flask_app() -> None:
    """Shutdown the Flask app subprocess when the MCP server exits."""
    global flask_process

    if flask_process:
        logger.info("Shutting down TIDAL Flask app...")
        flask_process.terminate()
        try:
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            flask_process.kill()
        logger.info("TIDAL Flask app shutdown complete")


# --- Error / Validation Helpers ---


def error_response(message: str) -> dict:
    """Create standardized error response dict."""
    return {"status": "error", "message": message}


def check_tidal_auth(action: str = "perform this action") -> dict | None:
    """
    Check if user is authenticated with TIDAL.

    Args:
        action: Description of the action requiring authentication

    Returns:
        Error dict if not authenticated, None if OK
    """
    try:
        auth_check = http.get(f"{FLASK_APP_URL}/api/auth/status", timeout=DEFAULT_TIMEOUT)
        auth_data = auth_check.json()

        if not auth_data.get("authenticated", False):
            return error_response(
                f"You need to login to TIDAL first before you can {action}. Please use the tidal_login() function."
            )
    except requests.RequestException as e:
        return error_response(f"Failed to check authentication status: {e}")

    return None


def handle_api_response(response: requests.Response, resource_name: str, resource_id: str = None) -> dict | None:
    """
    Handle common HTTP response patterns from the Flask API.

    Args:
        response: requests.Response object
        resource_name: Name of the resource (e.g., "playlist", "track")
        resource_id: Optional ID of the resource for error messages

    Returns:
        Error dict if response indicates an error, None if OK (200)
    """
    if response.status_code == 200:
        return None

    if response.status_code == 401:
        return error_response("Not authenticated with TIDAL. Please login first using tidal_login().")

    if response.status_code == 404:
        id_part = f" with ID {resource_id}" if resource_id else ""
        return error_response(
            f"{resource_name.capitalize()}{id_part} not found. Please check the {resource_name} ID and try again."
        )

    if response.status_code == 403:
        return error_response(f"Cannot modify this {resource_name} - you can only modify your own {resource_name}s.")

    try:
        error_data = response.json()
        error_msg = error_data.get("error", "Unknown error")
    except requests.JSONDecodeError:
        error_msg = "Unknown error"

    return error_response(f"Failed to access {resource_name}: {error_msg}")


def validate_list(value, field_name: str, item_type: str = "item") -> dict | None:
    """
    Validate that a value is a non-empty list.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        item_type: Type of items in the list for error messages

    Returns:
        Error dict if validation fails, None if OK
    """
    if not value or not isinstance(value, list) or len(value) == 0:
        return error_response(f"At least one {item_type} is required. Please provide {field_name}.")
    return None


def validate_string(value, field_name: str) -> dict | None:
    """
    Validate that a value is a non-empty string.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Returns:
        Error dict if validation fails, None if OK
    """
    if not value or (isinstance(value, str) and not value.strip()):
        return error_response(f"A {field_name} is required.")
    return None


# --- Shared MCP HTTP helpers ---


def mcp_get(endpoint: str, resource: str, params: dict = None, resource_id: str = None) -> dict:
    """
    Standard GET pattern for MCP tools.

    Args:
        endpoint: API endpoint path (e.g., "/api/tracks")
        resource: Resource name for error messages
        params: Optional query parameters
        resource_id: Optional resource ID for error messages

    Returns:
        Parsed JSON response dict, or error dict on failure
    """
    response = http.get(f"{FLASK_APP_URL}{endpoint}", params=params, timeout=DEFAULT_TIMEOUT)
    error = handle_api_response(response, resource, resource_id)
    return error if error else response.json()


def mcp_post(endpoint: str, resource: str, payload: dict = None, resource_id: str = None) -> dict:
    """
    Standard POST pattern for MCP tools.

    Args:
        endpoint: API endpoint path
        resource: Resource name for error messages
        payload: JSON body
        resource_id: Optional resource ID for error messages

    Returns:
        Parsed JSON response dict, or error dict on failure
    """
    response = http.post(f"{FLASK_APP_URL}{endpoint}", json=payload, timeout=DEFAULT_TIMEOUT)
    error = handle_api_response(response, resource, resource_id)
    return error if error else response.json()


def mcp_delete(endpoint: str, resource: str, payload: dict = None, resource_id: str = None) -> dict:
    """
    Standard DELETE pattern for MCP tools.

    Args:
        endpoint: API endpoint path
        resource: Resource name for error messages
        payload: Optional JSON body
        resource_id: Optional resource ID for error messages

    Returns:
        Parsed JSON response dict, or error dict on failure
    """
    kwargs = {"timeout": DEFAULT_TIMEOUT}
    if payload is not None:
        kwargs["json"] = payload
    response = http.delete(f"{FLASK_APP_URL}{endpoint}", **kwargs)
    error = handle_api_response(response, resource, resource_id)
    return error if error else response.json()


def mcp_patch(endpoint: str, resource: str, payload: dict = None, resource_id: str = None) -> dict:
    """
    Standard PATCH pattern for MCP tools.

    Args:
        endpoint: API endpoint path
        resource: Resource name for error messages
        payload: JSON body
        resource_id: Optional resource ID for error messages

    Returns:
        Parsed JSON response dict, or error dict on failure
    """
    response = http.patch(f"{FLASK_APP_URL}{endpoint}", json=payload, timeout=DEFAULT_TIMEOUT)
    error = handle_api_response(response, resource, resource_id)
    return error if error else response.json()
