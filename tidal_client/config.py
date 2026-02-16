"""TIDAL API configuration constants"""


class Config:
    """Configuration for TIDAL API client"""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

        # API endpoints
        self.api_v1_url = "https://api.tidal.com/v1/"
        self.auth_token_url = "https://auth.tidal.com/v1/oauth2/token"
        self.device_auth_url = "https://auth.tidal.com/v1/oauth2/device_authorization"

        # Request defaults
        self.default_timeout = 30
        self.default_limit = 50
