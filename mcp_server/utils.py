import subprocess
import os
import pathlib
import shutil

import requests

# Define a configurable port with a default that's less likely to conflict
DEFAULT_PORT = 5050
FLASK_PORT = int(os.environ.get("TIDAL_MCP_PORT", DEFAULT_PORT))

# Define the base URL for your Flask app using the configurable port
FLASK_APP_URL = f"http://127.0.0.1:{FLASK_PORT}"

# Define the path to the Flask app dynamically
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
FLASK_APP_PATH = os.path.join(CURRENT_DIR, "..", "tidal_api", "app.py")
FLASK_APP_PATH = os.path.normpath(FLASK_APP_PATH)  # Normalize the path

# Find the path to uv executable
def find_uv_executable():
    """Find the uv executable in the path or common locations"""
    # First try to find in PATH
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    
    # Check common installation locations
    common_locations = [
        os.path.expanduser("~/.local/bin/uv"),  # Linux/macOS local install
        os.path.expanduser("~/AppData/Local/Programs/Python/Python*/Scripts/uv.exe"),  # Windows
        "/usr/local/bin/uv",  # macOS Homebrew
        "/opt/homebrew/bin/uv",  # macOS Apple Silicon Homebrew
    ]
    
    for location in common_locations:
        # Handle wildcards in paths
        if "*" in location:
            import glob
            matches = glob.glob(location)
            for match in matches:
                if os.path.isfile(match) and os.access(match, os.X_OK):
                    return match
        elif os.path.isfile(location) and os.access(location, os.X_OK):
            return location
    
    # If we can't find it, just return "uv" and let the system try to resolve it
    return "uv"

# Global variable to hold the Flask app process
flask_process = None

def start_flask_app():
    """Start the Flask app as a subprocess"""
    global flask_process
    
    print("Starting TIDAL Flask app...")
    
    # Find uv executable
    uv_executable = find_uv_executable()
    print(f"Using uv executable: {uv_executable}")
    
    # Start the Flask app using uv
    flask_process = subprocess.Popen([
        uv_executable, "run",
        "--with", "tidalapi",
        "--with", "flask",
        "--with", "requests",
        "python", FLASK_APP_PATH
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    # Optional: Read a few lines to ensure the app starts properly
    for _ in range(5):  # Read first 5 lines of output
        line = flask_process.stdout.readline()
        if line:
            print(f"Flask app: {line.decode().strip()}")
    
    print("TIDAL Flask app started")

def shutdown_flask_app():
    """Shutdown the Flask app subprocess when the MCP server exits"""
    global flask_process
    
    if flask_process:
        print("Shutting down TIDAL Flask app...")
        # Try to terminate gracefully first
        flask_process.terminate()
        try:
            # Wait up to 5 seconds for process to terminate
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't terminate in time, force kill it
            flask_process.kill()
        print("TIDAL Flask app shutdown complete")


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
        auth_check = requests.get(f"{FLASK_APP_URL}/api/auth/status")
        auth_data = auth_check.json()

        if not auth_data.get("authenticated", False):
            return error_response(
                f"You need to login to TIDAL first before you can {action}. "
                "Please use the tidal_login() function."
            )
    except Exception as e:
        return error_response(f"Failed to check authentication status: {str(e)}")

    return None


def handle_api_response(response, resource_name: str, resource_id: str = None) -> dict | None:
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
        return error_response(
            "Not authenticated with TIDAL. Please login first using tidal_login()."
        )

    if response.status_code == 404:
        id_part = f" with ID {resource_id}" if resource_id else ""
        return error_response(
            f"{resource_name.capitalize()}{id_part} not found. "
            f"Please check the {resource_name} ID and try again."
        )

    if response.status_code == 403:
        return error_response(
            f"Cannot modify this {resource_name} - you can only modify your own {resource_name}s."
        )

    # Generic error
    try:
        error_data = response.json()
        error_msg = error_data.get("error", "Unknown error")
    except Exception:
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
        return error_response(
            f"At least one {item_type} is required. "
            f"Please provide {field_name}."
        )
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