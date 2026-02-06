# Artist Tools

## get_artist_info

Get detailed information about a TIDAL artist including biography and roles.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artist_id` | string | *(required)* | The TIDAL artist ID |

### Example Prompts

- *"Tell me about Khruangbin"*
- *"Who is Radiohead?"*
- *"Get info on artist 3575920"*

### Response

```json
{
  "status": "success",
  "id": 3575920,
  "name": "Khruangbin",
  "bio": "Khruangbin is a three-piece band from Houston, Texas...",
  "roles": ["MAIN"],
  "picture_url": "https://resources.tidal.com/images/.../320x320.jpg",
  "url": "https://tidal.com/browse/artist/3575920"
}
```

---

## get_artist_top_tracks

Get an artist's most popular tracks on TIDAL.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artist_id` | string | *(required)* | The TIDAL artist ID |
| `limit` | int | 20 | Maximum tracks to return |

### Example Prompts

- *"What are Radiohead's top songs?"*
- *"Show me the most popular tracks by Khruangbin"*

### Response

```json
{
  "status": "success",
  "artist_id": "3575920",
  "tracks": [
    {"id": 123, "title": "Track Name", "artist": "Artist", "album": "Album", "duration": 240, "url": "..."}
  ],
  "total": 20
}
```

---

## get_artist_albums

Get an artist's albums, EPs/singles, or compilation appearances.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artist_id` | string | *(required)* | The TIDAL artist ID |
| `filter` | string | `"albums"` | Release type: `"albums"`, `"ep_singles"`, or `"other"` |
| `limit` | int | 50 | Maximum albums to return |

### Example Prompts

- *"Show me Radiohead's albums"*
- *"List all EPs and singles by Khruangbin"*
- *"What's in their discography?"*

### Response

```json
{
  "status": "success",
  "artist_id": "3575920",
  "filter": "albums",
  "albums": [
    {"id": 456, "name": "Album Name", "artist": "Artist", "release_date": "2024-01-15", "num_tracks": 12, "url": "..."}
  ],
  "total": 5
}
```

---

## get_similar_artists

Get artists similar to a given TIDAL artist.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artist_id` | string | *(required)* | The TIDAL artist ID |

### Example Prompts

- *"Who is similar to Khruangbin?"*
- *"Find artists like Radiohead"*
- *"Recommend similar artists"*

### Response

```json
{
  "status": "success",
  "artist_id": "3575920",
  "artists": [
    {"id": 789, "name": "Similar Artist", "picture_url": "...", "url": "..."}
  ],
  "total": 10
}
```

---

## get_artist_radio

Get a radio mix of tracks based on a TIDAL artist. Returns up to 100 tracks (TIDAL limit).

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artist_id` | string | *(required)* | The TIDAL artist ID |
| `limit` | int | 50 | Maximum tracks to return (max: 100) |

### Example Prompts

- *"Play Khruangbin radio"*
- *"Create a mix based on Radiohead"*
- *"Give me tracks inspired by this artist"*

### Response

```json
{
  "status": "success",
  "artist_id": "3575920",
  "tracks": [
    {"id": 101, "title": "Radio Track", "artist": "Some Artist", "album": "Some Album", "duration": 200, "url": "..."}
  ],
  "total": 50
}
```
