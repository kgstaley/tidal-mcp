# Troubleshooting

## Authentication Issues

**Browser doesn't open for login**
- Ensure your default browser is set correctly in your system settings
- Try manually opening the URL that Claude provides in the response

**Session expired**
- Simply ask Claude to log in again: *"Please log me in to TIDAL"*
- Sessions typically last several days before requiring re-authentication

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
