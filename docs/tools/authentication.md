# Authentication Tools

## tidal_login

Authenticate with TIDAL through a browser-based OAuth login flow. Opens your default browser to TIDAL's login page.

### Parameters

None.

### Example Prompts

- *"Please log me in to TIDAL"*
- *"Authenticate with TIDAL"*

### Response

```json
{
  "status": "success",
  "message": "Successfully logged in to TIDAL"
}
```

### Notes

- Your session is stored locally on your machine — no credentials are sent to Claude or external services.
- Sessions typically last several days before requiring re-authentication.
- If the browser doesn't open, try manually navigating to the URL provided in the response.
