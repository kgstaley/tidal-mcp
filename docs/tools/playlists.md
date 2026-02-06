# Playlist Tools

## get_user_playlists

List all your TIDAL playlists.

### Parameters

None.

### Example Prompts

- *"Show me all my playlists"*
- *"What playlists do I have on TIDAL?"*

### Response

```json
{
  "status": "success",
  "playlists": [
    {
      "id": "abc-123",
      "name": "My Playlist",
      "description": "A great playlist",
      "num_tracks": 42,
      "url": "https://tidal.com/playlist/abc-123"
    }
  ]
}
```

---

## get_playlist_tracks

Get all tracks from a specific playlist.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `limit` | int | 50 | Maximum tracks to retrieve (max: 5000) |

### Example Prompts

- *"Show me the tracks in my 'Chill Vibes' playlist"*
- *"List all songs in playlist abc-123"*

---

## create_tidal_playlist

Create a new playlist with specified tracks.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | string | *(required)* | Playlist title |
| `track_ids` | list[string] | *(required)* | Track IDs to add |
| `description` | string | `""` | Playlist description |

### Example Prompts

- *"Create a playlist called 'Late Night Jazz' with these tracks"*
- *"Make a new TIDAL playlist from my recommendations"*

---

## add_tracks_to_playlist

Add tracks to an existing playlist.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `track_ids` | list[string] | *(required)* | Track IDs to add |
| `allow_duplicates` | bool | `false` | Allow adding tracks already in the playlist |
| `position` | int | end | Position to insert tracks (0-indexed) |

### Example Prompts

- *"Add these 5 tracks to my 'Road Trip' playlist"*
- *"Add the search results to my workout playlist"*

---

## remove_tracks_from_playlist

Remove tracks from a playlist.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `track_ids` | list[string] | *(required)* | Track IDs to remove |

### Example Prompts

- *"Remove duplicate tracks from my playlist"*
- *"Delete the first 3 songs from my 'Old Mix' playlist"*

---

## delete_tidal_playlist

Delete a playlist from your account.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |

### Example Prompts

- *"Delete my 'Test Playlist'"*
- *"Remove the playlist I just created"*
