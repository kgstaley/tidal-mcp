# Task Completion Checklist

Before marking any task as complete, verify ALL items:

## Testing
- [ ] All tests pass: `uv run python3 -m pytest`
- [ ] No test warnings or deprecation notices
- [ ] New features have tests (Flask endpoints + MCP tools + formatters)
- [ ] Tests in correct location:
  - Flask tests → `tests/tidal_api/test_*.py`
  - MCP tests → `tests/mcp_server/test_*.py`
  - Shared mocks → `tests/conftest.py`

## Code Quality
- [ ] Linting passes: `ruff check .`
- [ ] Formatting correct: `ruff format --check .`
- [ ] Type hints on ALL new functions (args + return type)
- [ ] No `Any` types (use specific types)
- [ ] Constants defined (no magic numbers like `20`, `100`, `30`)

## Code Standards
- [ ] Absolute imports only (no relative imports)
- [ ] Imports grouped: stdlib, third-party, local
- [ ] No `print()` statements (use `logging`)
- [ ] HTTP requests have `timeout=30`
- [ ] Catch specific exceptions (no bare `except Exception`)
- [ ] Error logging includes `exc_info=True`
- [ ] f-strings everywhere (no `%` or `.format()`)

## Pattern Adherence
- [ ] Flask endpoints use `@requires_tidal_auth` decorator
- [ ] Flask endpoints use `@handle_endpoint_errors("action")` decorator
- [ ] MCP tools call `check_tidal_auth()` before API calls
- [ ] MCP tools use `validate_*()` for input validation
- [ ] Formatters follow base + detail pattern
- [ ] Used `safe_attr()` for nested attributes
- [ ] Used try/except for `.image()` method calls

## Documentation
- [ ] Updated CLAUDE.md if patterns changed
- [ ] Updated docs/patterns.md if new pattern added
- [ ] Commit message is clear and focused
- [ ] No "Co-Authored-By" lines in commit

## Git
- [ ] Changes are focused (one logical change per commit)
- [ ] Branch name matches feature: `feature/description`
- [ ] PR goes to fork (`kgstaley/tidal-mcp`), not upstream
- [ ] Use `gh pr create --draft --repo kgstaley/tidal-mcp`

## tidalapi Verification
- [ ] Checked installed library source if using new tidalapi methods
- [ ] Verified method signatures in `.venv/lib/python3.10/site-packages/tidalapi/`
- [ ] Used correct attribute vs method (e.g., `.picture` vs `.image()`)
- [ ] Used correct image dimensions (artists: 160,320,480,750; albums: 80,160,320,640,1280)

## Quick Verification Commands
```bash
# Run all checks
uv run python3 -m pytest && ruff check . && ruff format --check .

# Check for print statements
grep -r "print(" tidal_api/ mcp_server/ --include="*.py" | grep -v "__pycache__"

# Check for missing timeouts
grep -r "requests\." tidal_api/ mcp_server/ --include="*.py" | grep -v "timeout"

# Check for bare except
grep -r "except:" tidal_api/ mcp_server/ --include="*.py" | grep -v "# noqa"
```

## Common Gotchas
- ❌ `except Exception:` → ✅ `except requests.RequestException:`
- ❌ `print(debug_info)` → ✅ `logging.debug(debug_info)`
- ❌ `requests.get(url)` → ✅ `requests.get(url, timeout=30)`
- ❌ `LIMIT = 20` inline → ✅ `DEFAULT_LIMIT = 20` at module level
- ❌ `from .utils import foo` → ✅ `from tidal_api.utils import foo`
- ❌ `artist.picture(320)` → ✅ `artist.image(320)` (method, not attribute)
- ❌ `results.tracks` → ✅ `results.get('tracks', [])` (dict, not object)
