# Code Style

## Language & Typing
- **Python 3.10+** with modern syntax features
- **Type hints** on ALL function signatures (args + return type)
- Use `Optional[T]` for nullable types, `List[T]` for lists, `Dict[K, V]` for dicts
- Avoid `Any` unless absolutely necessary

## Imports
- **Absolute imports only** (no relative imports)
- **Grouped in order**: stdlib, third-party, local modules
- **No star imports** (`from module import *`)
- **One import per line** for local modules
- Example:
```python
# Standard library
import logging
from typing import Optional, List

# Third-party
from flask import Blueprint, jsonify, request
import tidalapi

# Local
from tidal_api.utils import format_track_data
from tidal_api.browser_session import get_tidal_session
```

## Naming Conventions
- **snake_case**: Functions, variables, module names (`format_artist_data`, `get_track_by_id`)
- **PascalCase**: Classes (`MockArtist`, `TidalSession`)
- **UPPER_SNAKE**: Constants (`MAX_LIMIT`, `DEFAULT_TIMEOUT`, `BASE_URL`)
- **No single-letter variables** except loop counters (`i`, `j`)

## Formatting
- **ruff format**: Auto-formatter (PEP 8 compliant)
- **120 character line length** (configured in pyproject.toml)
- **f-strings everywhere** (no `%` formatting or `.format()`)
- **Trailing commas** in multi-line structures
- **Two blank lines** between top-level definitions

## Constants
- **No magic numbers**: Define as module-level constants
- **Group related constants** together
- Example:
```python
# Pagination
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# Timeouts
DEFAULT_TIMEOUT = 30
AUTH_TIMEOUT = 60
```

## Error Handling
- **Catch specific exceptions**, never bare `except Exception:`
- **MCP tools**: Catch `requests.RequestException` (covers all HTTP errors)
- **Flask routes**: Use `@handle_endpoint_errors` decorator
- **Always log errors** with `logging.error(..., exc_info=True)`
- Example:
```python
try:
    response = session.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logging.error(f"Failed to fetch data: {e}", exc_info=True)
    raise
```

## Logging
- **Use `logging` module** (never `print()`)
- **Log levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Include context**: What failed, which entity, what was attempted
- **Use `exc_info=True`** for error tracebacks
- Example:
```python
logging.info(f"Fetching track {track_id}")
logging.error(f"Failed to fetch track {track_id}", exc_info=True)
```

## HTTP Requests
- **ALL requests** require `timeout=30` parameter
- **Use `response.raise_for_status()`** to check status codes
- **Catch `requests.RequestException`** (not bare Exception)
- Example:
```python
response = requests.get(url, timeout=30)
response.raise_for_status()
```

## Function Design
- **Single responsibility**: Each function does one thing
- **Type hints**: Required on all signatures
- **Docstrings**: Optional for simple functions, required for complex logic
- **Early returns**: Use guard clauses to reduce nesting
- Example:
```python
def format_track_data(track: tidalapi.Track) -> dict:
    """Format track data for API response."""
    if not track:
        return {}
    
    return {
        "id": track.id,
        "name": track.name,
        "duration": track.duration,
    }
```

## Testing
- **One test class per endpoint/tool**
- **Descriptive test names**: `test_endpoint_success`, `test_endpoint_not_found`
- **Use fixtures** from `tests/conftest.py`
- **Mock external dependencies** (tidalapi, HTTP requests)
- **Assert specific values**, not just truthiness
