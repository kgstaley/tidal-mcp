# TIDAL Client Architecture

## Overview

Custom TIDAL API client replacing `tidalapi` for direct control over OAuth flows, request handling, and error management.

## Package Structure

```
tidal_client/
├── __init__.py         # Package exports (TidalSession, Config, exceptions)
├── config.py           # Configuration (API URLs, OAuth credentials)
├── session.py          # TidalSession class (main client interface)
├── auth.py             # OAuth device flow functions
├── exceptions.py       # Exception hierarchy
├── models/             # TypedDict response models (future)
└── endpoints/          # API endpoint functions (future)
```

## Core Components

### 1. Config (`config.py`)

Centralized configuration for API URLs and OAuth credentials.

```python
class Config:
    """TIDAL API configuration."""
    
    # API Base URLs
    API_BASE_URL: str = "https://api.tidal.com/v1"
    AUTH_BASE_URL: str = "https://auth.tidal.com/v1/oauth2"
    
    # OAuth Client Credentials
    CLIENT_ID: str = "..."      # TIDAL client ID
    CLIENT_SECRET: str = "..."  # TIDAL client secret
```

**Usage:**
- Import and use `Config.API_BASE_URL`, `Config.CLIENT_ID`, etc.
- All URLs and credentials in one place for easy updates

### 2. TidalSession (`session.py`)

Main client class managing OAuth tokens and HTTP requests.

**Key Methods:**

```python
class TidalSession:
    def __init__(self, access_token: str = None, refresh_token: str = None, ...):
        """Initialize session with optional tokens."""
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated HTTP request to TIDAL API."""
        # 1. Add Authorization header
        # 2. Auto-refresh token if expired
        # 3. Make request with timeout
        # 4. Raise TidalAPIError on failure
    
    def refresh_access_token(self) -> None:
        """Refresh access token using refresh token."""
        # Calls refresh_token() from auth.py
        # Updates self.access_token and self.expires_at
    
    def save_session(self, filepath: str) -> None:
        """Save session tokens to JSON file."""
    
    @classmethod
    def load_session(cls, filepath: str) -> "TidalSession":
        """Load session from JSON file."""
```

**Key Features:**
- **Automatic token refresh**: `request()` checks expiry and refreshes if needed
- **Session persistence**: Save/load tokens to/from JSON files
- **Error handling**: All HTTP errors wrapped in `TidalAPIError`

### 3. OAuth Functions (`auth.py`)

Device flow OAuth implementation (no browser required).

```python
def start_device_auth() -> dict:
    """Start OAuth device flow."""
    # Returns: {
    #   "device_code": "...",
    #   "user_code": "...",
    #   "verification_uri": "...",
    #   "expires_in": 300
    # }

def poll_for_token(device_code: str, interval: int = 5) -> dict:
    """Poll for access token until user authorizes."""
    # Polls every `interval` seconds
    # Returns: {
    #   "access_token": "...",
    #   "refresh_token": "...",
    #   "expires_in": 3600
    # }

def refresh_token(refresh_token: str) -> dict:
    """Refresh access token using refresh token."""
    # Returns: {
    #   "access_token": "...",
    #   "refresh_token": "...",  # May be new token
    #   "expires_in": 3600
    # }
```

**OAuth Flow:**
1. Call `start_device_auth()` → Get user code and verification URI
2. Display code to user → User visits URI and enters code
3. Call `poll_for_token(device_code)` → Wait for user authorization
4. Receive tokens → Create `TidalSession` with tokens
5. Automatic refresh → `TidalSession.request()` auto-refreshes when needed

### 4. Exception Hierarchy (`exceptions.py`)

Custom exceptions for specific error handling.

```python
class TidalClientError(Exception):
    """Base exception for all tidal_client errors."""

class TidalAPIError(TidalClientError):
    """API request failed."""
    # Includes: status_code, response_text

class TidalAuthError(TidalClientError):
    """Authentication/OAuth error."""

class TidalTokenExpiredError(TidalAuthError):
    """Access token expired and refresh failed."""

class TidalRateLimitError(TidalAPIError):
    """Rate limit exceeded."""
```

**Usage Pattern:**
```python
try:
    session.request("GET", "/tracks/123")
except TidalTokenExpiredError:
    # Re-authenticate user
except TidalRateLimitError:
    # Back off and retry
except TidalAPIError as e:
    # Log error with e.status_code and e.response_text
```

## Design Principles

### 1. Explicit Token Management
- No hidden session state
- Tokens passed explicitly to `TidalSession.__init__()`
- Save/load methods for persistence

### 2. Automatic Token Refresh
- `request()` method checks token expiry before each request
- Auto-refreshes using refresh token if expired
- Raises `TidalTokenExpiredError` if refresh fails

### 3. Type Safety
- Type hints on all function signatures
- Future: TypedDict models for API responses

### 4. Error Transparency
- Specific exceptions for different failure modes
- HTTP status codes and response text included in errors
- No silent failures or generic exceptions

### 5. Configuration Centralization
- All URLs and credentials in `Config` class
- Easy to update for different environments
- No magic strings in code

## Testing Strategy

### Test Coverage

**`test_config.py`:**
- Config class has correct URLs
- OAuth credentials are non-empty

**`test_session.py`:**
- Session initialization with/without tokens
- Token management (set, get, expiry check)
- HTTP request method (success, error, timeout)
- Save/load session to/from JSON

**`test_auth.py`:**
- Device flow start (success, error)
- Token polling (success, timeout, denied)
- Token refresh (success, invalid token)

**`test_exceptions.py`:**
- Exception hierarchy (inheritance)
- Exception messages and attributes

### Mock Patterns

**Mocking OAuth Responses:**
```python
@pytest.fixture
def mock_device_auth_response():
    return {
        "device_code": "test-device-code",
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://link.tidal.com/device",
        "expires_in": 300,
    }
```

**Mocking HTTP Requests:**
```python
def test_request_success(mock_requests):
    mock_requests.get.return_value = MockResponse(200, {"id": "123"})
    session = TidalSession(access_token="token")
    response = session.request("GET", "/tracks/123")
    assert response.status_code == 200
```

## Migration from tidalapi

### Current State (tidalapi)
```python
import tidalapi
session = tidalapi.Session()
session.login_oauth_simple()  # Browser OAuth
track = session.track("123")
```

### Future State (tidal_client)
```python
from tidal_client import TidalSession, start_device_auth, poll_for_token

# OAuth flow
auth_data = start_device_auth()
print(f"Visit {auth_data['verification_uri']} and enter {auth_data['user_code']}")
tokens = poll_for_token(auth_data['device_code'])

# Create session
session = TidalSession(
    access_token=tokens["access_token"],
    refresh_token=tokens["refresh_token"],
)

# Make requests (auto-refreshes tokens)
response = session.request("GET", "/tracks/123")
track_data = response.json()
```

### Migration Steps

1. **Phase 1: Foundation** (✅ COMPLETE)
   - Create package structure
   - Implement Config, exceptions
   - Implement TidalSession (init, token management, request)
   - Implement OAuth functions (device flow, polling, refresh)
   - Add tests for all components

2. **Phase 2: Endpoint Functions** (NEXT)
   - Create `endpoints/` modules (tracks, albums, artists, etc.)
   - Implement functions wrapping TIDAL API endpoints
   - Add TypedDict models for responses

3. **Phase 3: Integration**
   - Update `tidal_api/browser_session.py` to use tidal_client
   - Update Flask routes to use new client
   - Update tests to use new client

4. **Phase 4: Deprecation**
   - Remove tidalapi dependency
   - Update documentation
   - Remove tidalapi-specific code

## Key Differences from tidalapi

| Feature | tidalapi | tidal_client |
|---------|----------|--------------|
| OAuth Flow | Browser-based | Device flow (no browser) |
| Token Management | Hidden session state | Explicit tokens |
| Token Refresh | Automatic (opaque) | Automatic (transparent) |
| Error Handling | Generic exceptions | Specific exception hierarchy |
| Type Safety | Limited | Full type hints + TypedDict |
| Configuration | Hardcoded | Centralized Config class |
| API Coverage | Comprehensive objects | REST endpoints (TypedDict) |

## Next Steps

1. ✅ Foundation implementation (Config, Session, Auth, Exceptions)
2. ✅ Foundation tests (all passing)
3. 🔄 Endpoint functions (tracks, albums, artists, playlists, etc.)
4. 🔄 Response models (TypedDict for API responses)
5. 🔄 Integration with Flask backend
6. 🔄 Remove tidalapi dependency
