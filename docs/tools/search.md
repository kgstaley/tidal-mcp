# Search Tools

## search_tidal

Search the TIDAL catalog across multiple content types.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | Search query text |
| `types` | list[string] | all types | Content types to search: `"artists"`, `"tracks"`, `"albums"`, `"playlists"`, `"videos"` |
| `limit` | int | 20 | Maximum results per type |

### Example Prompts

- *"Search for Khruangbin on TIDAL"*
- *"Find albums by Radiohead"*
- *"Search for 'lo-fi beats' playlists"*

### Response

```json
{
  "status": "success",
  "query": "Khruangbin",
  "artists": [{"id": 123, "name": "Khruangbin", ...}],
  "tracks": [...],
  "albums": [...],
  "playlists": [...],
  "videos": [...],
  "top_hit": {"type": "artist", "data": {...}}
}
```
