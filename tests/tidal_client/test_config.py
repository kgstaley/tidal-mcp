"""Tests for TIDAL API configuration constants"""

from tidal_client.config import Config


def test_config_has_api_urls():
    """Config should provide TIDAL API URLs"""
    config = Config(client_id="test_id", client_secret="test_secret")

    assert config.api_v1_url == "https://api.tidal.com/v1/"
    assert config.auth_token_url == "https://auth.tidal.com/v1/oauth2/token"
    assert config.device_auth_url == "https://auth.tidal.com/v1/oauth2/device_authorization"


def test_config_stores_credentials():
    """Config should store OAuth credentials"""
    config = Config(client_id="my_id", client_secret="my_secret")

    assert config.client_id == "my_id"
    assert config.client_secret == "my_secret"
