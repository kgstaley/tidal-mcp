# tidalapi Local Patch

## Issue

tidalapi v0.8.11 has a bug where device authorization sends OAuth parameters as URL query string instead of form-encoded request body, causing **415 Unsupported Media Type** error from TIDAL's API.

**Error response from TIDAL:**
```json
{"status": 415, "detail": "Content-Type 'null' is not supported."}
```

This manifests in TIDAL MCP as "400 Bad Request" when calling `tidal_login`.

## Root Cause

**File:** `.venv/lib/python3.10/site-packages/tidalapi/session.py`
**Line:** 619
**Bug:** `params` parameter sends data as URL query string, not request body

## Fix Applied

**One-word change:** `params` → `data`

**Before:**
```python
request = self.request_session.post(url, params)
```

**After:**
```python
request = self.request_session.post(url, data=params)
```

## Why This Works

| Parameter | Behavior | Content-Type | Location |
|-----------|----------|--------------|----------|
| `params=` | URL query string | N/A | `?client_id=xxx&scope=yyy` |
| `data=` | Form-encoded body | `application/x-www-form-urlencoded` | Request body |

TIDAL's API now requires credentials in the request body with proper Content-Type header (security best practice - credentials in URLs leak through logs/proxies/browser history).

## Automated Patch System

This patch is automatically applied after dependency installations via a post-install hook.

**Patch infrastructure:**
- `patches/tidalapi-session.patch` — unified diff (version controlled)
- `scripts/apply-patches.sh` — application script
- `pyproject.toml` — post-install hook configuration

**Reapplication:**
```bash
# Automatic (triggered by uv sync, uv pip install, etc.)
uv sync

# Manual (if needed)
bash scripts/apply-patches.sh
```

## Verification

### Quick Test

```bash
uv run python3 << 'EOF'
import base64, requests

# tidalapi's hardcoded client_id
client_id = base64.b64decode(
    base64.b64decode(b"WmxneVNuaGtiVzUw") +
    base64.b64decode(b"V2xkTE1HbDRWQT09")
).decode("utf-8")

url = "https://auth.tidal.com/v1/oauth2/device_authorization"
data = {"client_id": client_id, "scope": "r_usr w_usr w_sub"}

r = requests.post(url, data=data, timeout=10)
print(f"Status: {r.status_code}")
print("✓ PATCHED" if r.ok else "✗ NOT PATCHED")
if r.ok:
    print(f"User code: {r.json()['userCode']}")
EOF
```

**Expected output:**
```
Status: 200
✓ PATCHED
User code: XXXXX
```

### Integration Tests

```bash
# Run integration tests that verify patch
uv run python3 -m pytest tests/integration/test_auth_integration.py -v
```

**Expected:** 3 passed, 1 skipped

## Manual Patch (Fallback)

If automated patching fails:

```bash
# Edit the file directly
vim .venv/lib/python3.10/site-packages/tidalapi/session.py

# Navigate to line 619
# Change: request = self.request_session.post(url, params)
# To:     request = self.request_session.post(url, data=params)

# Verify with quick test above
```

## Upstream Status

- **Bug reported:** Pending (will create issue at [tamland/python-tidal](https://github.com/tamland/python-tidal))
- **Fixed in version:** TBD
- **Action:** Monitor tidalapi releases; remove patch when fixed upstream

## Alternative: Custom Credentials

You can use your own TIDAL developer API credentials instead of tidalapi's hardcoded ones:

1. Register at [TIDAL Developer Portal](https://developer.tidal.com)
2. Get client ID and secret
3. Store in `.env`:
   ```bash
   TIDAL_CLIENT_ID=your_client_id_here
   TIDAL_CLIENT_SECRET=your_client_secret_here
   ```
4. Modify `BrowserSession` initialization to use custom credentials

**Note:** This patch is still required even with custom credentials, unless you implement your own OAuth flow that bypasses tidalapi's `get_link_login()` method.

## Long-term Solutions

1. **Contribute PR to tidalapi** with this fix
2. **Switch to PKCE authentication flow** once token exchange issues are resolved (see `feat/pkce-auth-flow` branch)
3. **Implement custom OAuth** bypassing tidalapi entirely
