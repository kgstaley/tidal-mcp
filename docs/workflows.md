# Common Workflows

## Getting Personalized Recommendations

```
You: "Based on my recent favorites, recommend some similar tracks but more upbeat and from the last 2 years"
Claude: [Uses get_favorite_tracks → recommend_tracks → presents curated list]
```

## Searching and Adding to Playlists

```
You: "Search for songs by Khruangbin and add the top 5 to my 'Chill Vibes' playlist"
Claude: [Uses search_tidal → get_user_playlists → add_tracks_to_playlist]
```

## Creating a Themed Playlist

```
You: "Create a playlist called 'Late Night Jazz' with recommendations based on my playlist 'Evening Relaxation'"
Claude: [Uses get_playlist_tracks → recommend_tracks → create_tidal_playlist]
```

## Cleaning Up Playlists

```
You: "Show me my playlist 'Road Trip Mix' and remove any duplicate tracks"
Claude: [Uses get_playlist_tracks → remove_tracks_from_playlist]
```

## Prompt Starters

**Recommendations**
- *"Recommend songs like those in this playlist, but slower and more acoustic."*
- *"Create a playlist based on my top tracks, but focused on chill, late-night vibes."*
- *"Find songs like these in playlist XYZ but in languages other than English."*

**Search & Discovery**
- *"Search for albums by Radiohead and show me their most recent releases."*
- *"Find tracks similar to 'Bohemian Rhapsody' and add them to a new playlist."*

**Playlist Management**
- *"Add the top 10 results from searching 'lo-fi beats' to my study playlist."*
- *"Remove any tracks by artist X from my workout playlist."*
- *"Show me all my playlists and how many tracks each has."*

**Tips**
- Use more tracks as seeds to broaden the inspiration.
- Return more recommendations if you want a longer playlist.
- Delete a playlist if you're not into it — no pressure!
