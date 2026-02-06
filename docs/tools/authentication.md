# Authentication Tools

## tidal_login

Authenticate with TIDAL through a browser-based login flow. Opens your default browser to TIDAL's login page.

The auth flow used depends on your configuration:

- **PKCE flow** (when `TIDAL_CLIENT_ID` is set): Browser opens TIDAL's login page, TIDAL redirects back to a local callback, tokens are exchanged automatically. The tool polls until auth completes.
- **Device code flow** (default): Browser opens with a pre-filled device code, user confirms on TIDAL's site.

### Parameters

None.

### Example Prompts

- *"Please log me in to TIDAL"*
- *"Authenticate with TIDAL"*

### Response

```json
{
  "status": "success",
  "message": "Successfully authenticated with TIDAL",
  "user": {
    "id": 123456,
    "username": "your_username",
    "email": "your_email"
  }
}
```

### Notes

- Your session is stored locally on your machine — no credentials are sent to Claude or external services.
- Sessions typically last several days before requiring re-authentication.
- If the browser doesn't open, try manually navigating to the URL provided in the response.
- PKCE flow has a 120-second timeout — if you don't complete login in time, try again.
- If using custom credentials, ensure your redirect URI in the TIDAL Developer Portal matches `http://localhost:{port}/api/auth/callback`.
