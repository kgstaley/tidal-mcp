# Suggested Commands

## Testing
```bash
# Run all tests
uv run python3 -m pytest

# Run tests with verbose output
uv run python3 -m pytest -v

# Run single test file
uv run python3 -m pytest tests/path/to/test_file.py

# Run specific test class
uv run python3 -m pytest tests/path/to/test_file.py::TestClassName

# Run with coverage
uv run python3 -m pytest --cov=tidal_api --cov=mcp_server
```

## Linting & Formatting
```bash
# Lint code (check for issues)
ruff check .

# Format code (apply changes)
ruff format .

# Check formatting without applying changes
ruff format --check .

# Auto-fix safe linting issues
ruff check --fix .
```

## Development
```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate

# Check Python version
python --version  # Should be 3.10+

# Install tidalapi from source (if needed)
uv pip install -e /path/to/tidalapi
```

## Git (via gh CLI)
```bash
# Create draft PR to fork
gh pr create --draft --repo kgstaley/tidal-mcp

# View PR status
gh pr status

# List branches
git branch -a

# Check status
git status

# View diff
git diff

# View commit history
git log --oneline -10
```

## System (Darwin/macOS)
```bash
# List files
ls -lah

# Find files
find . -name "*.py" -type f

# Search file contents
grep -r "pattern" --include="*.py"

# Navigate directories
cd /Users/kerrychristinestaley/code/tidal-mcp

# Check which Python
which python3
```

## Runtime
```bash
# Set custom port for Flask backend
export TIDAL_MCP_PORT=8080

# Run MCP server directly (for testing)
python3 -m mcp_server.server

# Check if Flask is running
lsof -i :5050
```
