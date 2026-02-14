# tests/tidal_client/conftest.py
"""Shared fixtures for tidal_client tests"""
import pytest
import responses


@pytest.fixture
def mock_config():
    """Mock Config object for testing"""
    from tidal_client.config import Config
    return Config(client_id="test_client_id", client_secret="test_secret")


@pytest.fixture
def mock_api_response():
    """Mock successful API response"""
    with responses.RequestsMock() as rsps:
        yield rsps
