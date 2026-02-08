#!/bin/bash
# Apply patches to installed dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PATCH_FILE="$PROJECT_ROOT/patches/tidalapi-session.patch"

# Find Python version directory
SITE_PACKAGES=$(find "$PROJECT_ROOT/.venv/lib" -type d -name "site-packages" 2>/dev/null | head -1)

if [ -z "$SITE_PACKAGES" ]; then
    echo "Error: Could not find site-packages directory in .venv"
    exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
    echo "Error: Patch file not found at $PATCH_FILE"
    exit 1
fi

echo "Applying tidalapi authentication patch..."
echo "  Patch file: $PATCH_FILE"
echo "  Target: $SITE_PACKAGES/tidalapi/session.py"

# Apply patch (use -p1 to strip the leading a/ and b/ from paths)
# The -d flag sets the working directory for patch application
if patch -p1 -d "$SITE_PACKAGES" < "$PATCH_FILE" 2>/dev/null; then
    echo "✓ tidalapi patch applied successfully"
elif patch -p1 -d "$SITE_PACKAGES" -R --dry-run < "$PATCH_FILE" > /dev/null 2>&1; then
    echo "✓ tidalapi patch already applied (skipped)"
else
    echo "✗ Failed to apply patch"
    exit 1
fi
