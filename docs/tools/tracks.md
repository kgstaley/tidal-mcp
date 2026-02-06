# Track Tools

## get_favorite_tracks

Retrieve your saved/favorite tracks from TIDAL with automatic pagination.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Maximum tracks to retrieve (max: 5000) |

### Example Prompts

- *"Show me my favorite tracks"*
- *"Get my last 100 saved songs on TIDAL"*

### Response

```json
{
  "status": "success",
  "count": 50,
  "tracks": [
    {
      "id": 123456,
      "title": "Track Name",
      "artist": "Artist Name",
      "album": "Album Name",
      "duration": 240,
      "url": "https://tidal.com/track/123456"
    }
  ]
}
```

---

## recommend_tracks

Get personalized track recommendations based on seed tracks or your favorites.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_ids` | list[string] | None | Specific track IDs to use as seeds |
| `filter_criteria` | string | None | Natural language filter (e.g., "upbeat and recent") |
| `limit_per_track` | int | 5 | Recommendations per seed track |
| `limit_from_favorite` | int | 5 | Number of favorite tracks to use as seeds (when `track_ids` not provided) |

### Example Prompts

- *"Recommend tracks based on my recent favorites, but more upbeat"*
- *"Find similar tracks to these 5 songs"*
- *"Create recommendations from my favorites, only from the last 2 years"*

### Response

```json
{
  "status": "success",
  "recommendations": [
    {
      "id": 789012,
      "title": "Recommended Track",
      "artist": "Some Artist",
      "album": "Some Album",
      "url": "https://tidal.com/track/789012"
    }
  ],
  "seed_tracks": ["123456", "789012"]
}
```
