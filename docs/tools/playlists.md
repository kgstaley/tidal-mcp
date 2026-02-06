# Playlist Tools

Comprehensive playlist management tools for creating, reading, updating, and deleting TIDAL playlists.

## Read Operations

### get_user_playlists

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

### get_playlist_tracks

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

## Create & Delete

### create_tidal_playlist

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

### delete_tidal_playlist

Delete a playlist from your account.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |

#### Example Prompts

- *"Delete my 'Test Playlist'"*
- *"Remove the playlist I just created"*

---

## Modify Tracks

### add_tracks_to_playlist

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

### remove_tracks_from_playlist

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

### clear_tidal_playlist

Remove all tracks from a playlist without deleting the playlist itself.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `chunk_size` | int | `50` | Number of tracks to remove per batch |

**⚠️ Warning:** This operation is irreversible. All tracks will be permanently removed from the playlist.

#### Example Prompts

- *"Clear all songs from my 'Old Mix' playlist"*
- *"Empty my test playlist"*
- *"Remove all tracks from my workout playlist"*

#### Response

```json
{
  "status": "success",
  "message": "Playlist cleared successfully",
  "playlist_id": "abc-123",
  "playlist_url": "https://tidal.com/playlist/abc-123"
}
```

---

### reorder_tidal_playlist_tracks

Move one or more tracks to a different position in a playlist.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `indices` | list[int] | *(required)* | List of track positions to move (0-based) |
| `position` | int | *(required)* | Target position to move tracks to (0-based) |

**Note:** All positions use 0-based indexing (first track is position 0).

#### Example Prompts

- *"Move the first track in my playlist to the end"*
- *"Move tracks 2, 5, and 7 to position 10 in my workout playlist"*
- *"Reorder my playlist by moving the last 3 songs to the beginning"*

#### Response

```json
{
  "status": "success",
  "message": "Moved 3 track(s) to position 10",
  "playlist_id": "abc-123",
  "playlist_url": "https://tidal.com/playlist/abc-123"
}
```

---

### merge_tidal_playlists

Copy all tracks from one playlist into another. The source playlist is not modified.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_playlist_id` | string | *(required)* | The playlist to add tracks to |
| `source_playlist_id` | string | *(required)* | The playlist to copy tracks from |
| `allow_duplicates` | boolean | `false` | Whether to add tracks already in the target |
| `allow_missing` | boolean | `true` | Whether to continue if some tracks are unavailable |

#### Example Prompts

- *"Merge my 'Summer Hits' playlist into my 'Best of 2025' playlist"*
- *"Combine my two workout playlists"*
- *"Add all tracks from my 'Favorites' playlist to my 'Party Mix'"*

#### Response

```json
{
  "status": "success",
  "message": "Playlists merged successfully",
  "target_playlist_id": "abc-123",
  "source_playlist_id": "xyz-789",
  "tracks_added": 42,
  "target_playlist_url": "https://tidal.com/playlist/abc-123",
  "source_playlist_url": "https://tidal.com/playlist/xyz-789"
}
```

---

## Modify Metadata

### edit_tidal_playlist

Edit a playlist's title and/or description.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `title` | string | `None` | New playlist title |
| `description` | string | `None` | New playlist description |

**Note:** At least one of `title` or `description` must be provided.

#### Example Prompts

- *"Rename my 'Workout Mix' playlist to 'Gym Hits'"*
- *"Change the description of my 'Chill Vibes' playlist to 'Relaxing evening tunes'"*
- *"Update my road trip playlist with a new title and description"*

#### Response

```json
{
  "status": "success",
  "message": "Playlist updated successfully",
  "playlist": {
    "id": "abc-123",
    "name": "Updated Title",
    "description": "Updated description",
    "num_tracks": 42,
    "url": "https://tidal.com/playlist/abc-123"
  },
  "playlist_url": "https://tidal.com/playlist/abc-123"
}
```

---

### set_tidal_playlist_visibility

Set whether a playlist is public (shareable) or private.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_id` | string | *(required)* | The playlist UUID |
| `public` | boolean | *(required)* | `true` to make public, `false` to make private |

#### Example Prompts

- *"Make my 'Best of 2025' playlist public"*
- *"Set my workout playlist to private"*
- *"Change my playlist to public so I can share it"*

#### Response

```json
{
  "status": "success",
  "message": "Playlist is now public",
  "playlist_id": "abc-123",
  "public": true,
  "playlist_url": "https://tidal.com/playlist/abc-123"
}
```
