# TIDAL MCP Feature Expansion Plan

**Created:** 2025-02-05
**Status:** In Progress (Phase 0)
**Plan ID:** ad4bccc8-053f-4d50-8a59-f46e887cc434

## Summary
Add ~24 new MCP tools across 6 feature areas, with corresponding Flask endpoints and formatters. Current state: 10 MCP tools, 12 Flask endpoints, 99 tests.

---

## Modularization Strategy

Currently `app.py` (514 lines) and `server.py` (741 lines) are monolithic. Adding ~29 endpoints and ~24 tools to those files would push them past 1500+ lines. Break both into categorized modules using Flask Blueprints and grouped MCP tool registration.

### Flask Backend — Blueprint-per-domain (`tidal_api/`)

```
tidal_api/
├── app.py                    # Flask app factory, registers blueprints (slim)
├── browser_session.py        # unchanged
├── utils.py                  # shared formatters + helpers (grows with new formatters)
├── routes/
│   ├── __init__.py
│   ├── auth.py               # /api/auth/* (existing: login, status)
│   ├── tracks.py             # /api/tracks/* (existing: favorites, recommendations)
│   ├── playlists.py          # /api/playlists/* (existing CRUD + new edit/reorder/merge/visibility)
│   ├── search.py             # /api/search (existing)
│   ├── artists.py            # /api/artists/* (Phase 1 — NEW)
│   ├── albums.py             # /api/albums/* (Phase 2 — NEW)
│   ├── media.py              # /api/tracks/<id>, /api/tracks/<id>/lyrics (Phase 2 — NEW)
│   ├── favorites.py          # /api/favorites/* (Phase 4 — NEW)
│   ├── mixes.py              # /api/mixes/* (Phase 3 — NEW)
│   └── discovery.py          # /api/genres/*, /api/pages/* (Phase 6 — NEW)
```

### MCP Server — Tool modules (`mcp_server/`)

```
mcp_server/
├── server.py                 # FastMCP init, imports tool modules (slim)
├── utils.py                  # shared validation/error helpers
├── tools/
│   ├── __init__.py
│   ├── auth.py               # tidal_login (existing)
│   ├── tracks.py             # get_favorite_tracks, recommend_tracks (existing)
│   ├── playlists.py          # playlist CRUD tools (existing + Phase 5 new)
│   ├── search.py             # search_tidal (existing)
│   ├── artists.py            # Phase 1 tools (NEW)
│   ├── albums.py             # Phase 2 album tools (NEW)
│   ├── media.py              # Phase 2 track detail/lyrics tools (NEW)
│   ├── favorites.py          # Phase 4 tools (NEW)
│   ├── mixes.py              # Phase 3 tools (NEW)
│   └── discovery.py          # Phase 6 tools (NEW)
```

### Migration Approach (Phase 0)
Before adding new features, refactor existing code AND fix anti-patterns.

### Test Module Structure
```
tests/
├── conftest.py              # Shared mock classes
├── tidal_api/
│   ├── __init__.py
│   ├── conftest.py          # Flask fixtures
│   ├── test_auth.py
│   ├── test_tracks.py
│   ├── test_playlists.py
│   ├── test_search.py
│   └── ... (per phase)
├── mcp_server/
│   ├── __init__.py
│   ├── conftest.py          # MCP fixtures
│   ├── test_auth.py
│   ├── test_tracks.py
│   ├── test_playlists.py
│   ├── test_search.py
│   └── ... (per phase)
└── test_utils.py
```

---

## Phase 1: Artist Deep-Dive
- Flask: `/api/artists/<id>`, `/api/artists/<id>/top-tracks`, `/api/artists/<id>/albums`, `/api/artists/<id>/similar`, `/api/artists/<id>/radio`
- MCP: `get_artist_info`, `get_artist_top_tracks`, `get_artist_albums`, `get_similar_artists`, `get_artist_radio`

## Phase 2: Album & Track Details
- Flask: `/api/albums/<id>`, `/api/albums/<id>/tracks`, `/api/albums/<id>/similar`, `/api/albums/<id>/review`, `/api/tracks/<id>`, `/api/tracks/<id>/lyrics`
- MCP: `get_album_info`, `get_album_tracks`, `get_similar_albums`, `get_album_review`, `get_track_info`, `get_track_lyrics`

## Phase 3: Mixes & Radio
- Flask: `/api/mixes`, `/api/mixes/<mix_id>/tracks`
- MCP: `get_user_mixes`, `get_mix_tracks`

## Phase 4: Full Favorites CRUD
- Flask: GET/POST/DELETE for `/api/favorites/artists`, `/api/favorites/albums`, `/api/favorites/tracks`, plus GET `/api/favorites/videos`, `/api/favorites/mixes`
- MCP: `get_favorites(type)`, `add_favorite(type, id)`, `remove_favorite(type, id)`

## Phase 5: Playlist Enhancements
- Flask: PATCH `/api/playlists/<id>`, POST `/api/playlists/<id>/reorder`, PUT `/api/playlists/<id>/visibility`, POST `/api/playlists/merge`
- MCP: `edit_playlist`, `reorder_playlist_tracks`, `set_playlist_visibility`, `merge_playlists`

## Phase 6: Discovery & Browsing
- Flask: `/api/genres`, `/api/genres/<path>/items`, `/api/pages/home`, `/api/pages/explore`
- MCP: `get_genres`, `get_genre_items`, `get_home_page`, `get_explore_page`

---

## Implementation Order & Branching

0. `refactor/modularize-routes-tools` — Extract existing code into Blueprints + tool modules (no new features)
1. `feature/artist-deep-dive`
2. `feature/album-track-details`
3. `feature/mixes-radio`
4. `feature/favorites-crud`
5. `feature/playlist-enhancements`
6. `feature/discovery-browsing`

## Totals

| Metric | Before | After |
|--------|--------|-------|
| MCP Tools | 10 | ~34 |
| Flask Endpoints | 12 | ~41 |
| Tests | 99 | ~280 |
| Formatters | 6 | ~14 |
