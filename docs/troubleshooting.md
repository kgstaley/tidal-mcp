# Troubleshooting

## Authentication Issues

**Browser doesn't open for login**
- Ensure your default browser is set correctly in your system settings
- Try manually opening the URL that Claude provides in the response

**Session expired**
- Simply ask Claude to log in again: *"Please log me in to TIDAL"*
- Sessions typically last several days before requiring re-authentication

**"invalid_client" or "Client with token ... not found" errors**
- This means TIDAL has revoked the OAuth client credentials that `tidalapi` ships with
- **Quick fix**: Update `tidalapi` to the latest version (`uv pip install --upgrade tidalapi`)
- **Long-term fix**: Set your own credentials via `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET` environment variables in your MCP config (see [setup.md](setup.md#custom-oauth-credentials-optional))

**"Client is not a Limited Input Device client" error**
- Your custom TIDAL developer app credentials don't support the device code flow
- This is expected — when `TIDAL_CLIENT_ID` is set, the server automatically uses the PKCE flow instead
- If you're seeing this error, make sure `TIDAL_CLIENT_ID` is set in your MCP config

**PKCE login times out**
- The PKCE flow has a 120-second timeout for completing the browser login
- Ensure the redirect URI in your TIDAL Developer Portal matches `http://localhost:{port}/api/auth/callback`
- Check that no firewall or browser extension is blocking the localhost redirect
- If using a non-default port, set `TIDAL_REDIRECT_URI` to match your registered redirect URI

**"Token exchange failed" on callback page**
- The authorization code from TIDAL couldn't be exchanged for tokens
- Verify your `TIDAL_CLIENT_SECRET` is correct
- Try logging in again — authorization codes are single-use and expire quickly

## Connection Issues

**"Failed to connect to TIDAL service" errors**
- Verify the Flask backend is running (check for port conflicts)
- Try changing the port via `TIDAL_MCP_PORT` environment variable
- Restart Claude Desktop to reload the MCP server

**Port conflicts**
- Default port is 5050. If occupied, set a custom port in your MCP config:
  ```json
  "env": { "TIDAL_MCP_PORT": "5100" }
  ```

## Common Questions

**Where are my credentials stored?**
- Your TIDAL session is stored locally in your system's temp directory
- No credentials are sent to Claude or any external service

**Do I need a TIDAL subscription?**
- Yes, a TIDAL subscription is required to access the API features

**Why do some tracks not have recommendations?**
- Not all tracks in TIDAL's catalog have recommendation data available
- Try using different seed tracks if recommendations are sparse
