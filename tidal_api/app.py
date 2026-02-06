"""Flask application factory for TIDAL API."""

import logging
import os

from flask import Flask, jsonify

from tidal_api.routes import albums_bp, artists_bp, auth_bp, mixes_bp, playlists_bp, search_bp, tracks_bp

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(albums_bp)
    app.register_blueprint(artists_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(mixes_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"})

    return app


# Module-level app for backward compatibility with subprocess launch
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("TIDAL_MCP_PORT", 5050))
    logger.info("Starting Flask app on port %s", port)
    app.run(debug=True, port=port)
