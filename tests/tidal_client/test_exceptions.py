from tidal_client.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TidalAPIError,
)


def test_tidal_api_error_is_base_exception():
    """TidalAPIError should be base for all custom exceptions"""
    error = TidalAPIError("test error")
    assert isinstance(error, Exception)
    assert str(error) == "test error"


def test_authentication_error_inherits_from_base():
    """AuthenticationError should inherit from TidalAPIError"""
    error = AuthenticationError("auth failed")
    assert isinstance(error, TidalAPIError)
    assert isinstance(error, Exception)


def test_not_found_error_inherits_from_base():
    """NotFoundError should inherit from TidalAPIError"""
    error = NotFoundError("resource not found")
    assert isinstance(error, TidalAPIError)


def test_rate_limit_error_inherits_from_base():
    """RateLimitError should inherit from TidalAPIError"""
    error = RateLimitError("rate limit exceeded")
    assert isinstance(error, TidalAPIError)
