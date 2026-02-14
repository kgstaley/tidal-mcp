# tests/tidal_client/conftest.py
"""Shared fixtures for tidal_client tests"""
import pytest


@pytest.fixture
def mock_config():
    """Mock Config object for testing"""
    from tidal_client.config import Config
    return Config(client_id="test_client_id", client_secret="test_secret")
