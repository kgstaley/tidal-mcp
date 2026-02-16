"""Custom exceptions for TIDAL API client"""


class TidalAPIError(Exception):
    """Base exception for all TIDAL API errors"""

    pass


class AuthenticationError(TidalAPIError):
    """Authentication failed or token expired"""

    pass


class NotFoundError(TidalAPIError):
    """Resource not found (404)"""

    pass


class RateLimitError(TidalAPIError):
    """Rate limit exceeded (429)"""

    pass
