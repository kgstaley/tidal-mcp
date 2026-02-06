"""Flask application factory for TIDAL API."""

import os

from flask import Flask

from tidal_api.routes import auth_bp, playlists_bp, search_bp, tracks_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(search_bp)

    return app


# Module-level app for backward compatibility with subprocess launch
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("TIDAL_MCP_PORT", 5050))
    print(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)
