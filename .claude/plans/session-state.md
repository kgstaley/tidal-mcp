# Session State — Feature Expansion Plan

Last updated: 2026-02-05

## Current Branch

`feature/artist-deep-dive` — PR #5 (draft): https://github.com/kgstaley/tidal-mcp/pull/5

## Plan File

Full plan: `.claude/plans/clever-twirling-newell.md` (also at `.claude/plans/in-progress/2025-02-05-feature-expansion.md`)

## Phase Status

| Phase | Branch | Status | PR |
|-------|--------|--------|----|
| 0 — Modularize routes/tools | `refactor/modularize-routes-tools` | **Merged** | #4 |
| 1 — Artist deep-dive | `feature/artist-deep-dive` | **PR open (draft)** | #5 |
| 2 — Album & track details | — | Not started | — |
| 3 — Mixes & radio | — | Not started | — |
| 4 — Full favorites CRUD | — | Not started | — |
| 5 — Playlist enhancements | — | Not started | — |
| 6 — Discovery & browsing | — | Not started | — |

## Phase 1 Summary (Artist Deep-Dive)

3 commits on `feature/artist-deep-dive`:

1. `3a48d5c` — Add artist deep-dive endpoints, MCP tools, and tests
2. `3f63d9d` — Add artist docs, update CHANGELOG and CLAUDE.md
3. `bde6ee4` — Add fork preference and pagination note to CLAUDE.md

### What was added

**Flask endpoints** (`tidal_api/routes/artists.py`):
- `GET /api/artists/<id>` — artist info with bio and roles
- `GET /api/artists/<id>/top-tracks` — top tracks
- `GET /api/artists/<id>/albums` — albums with `?filter=albums|ep_singles|other`
- `GET /api/artists/<id>/similar` — similar artists
- `GET /api/artists/<id>/radio` — artist radio (truncated client-side, tidalapi hardcodes 100)

**MCP tools** (`mcp_server/tools/artists.py`):
- `get_artist_info`, `get_artist_top_tracks`, `get_artist_albums`, `get_similar_artists`, `get_artist_radio`

**Helpers/formatters** (`tidal_api/utils.py`):
- `get_entity_or_404()` — generic entity lookup
- `format_artist_detail_data()` — extends base with bio + serialized Role enums

**Bug fixes**:
- `format_artist_data`: `artist.image(320)` instead of `artist.picture(640)` (picture is a UUID string, not callable; 640 not a valid dim)
- Role enum serialization for JSON responses

**Tests**: 142 total (31 new artist tests)

### Key tidalapi v0.8.3 learnings

Verified against installed source at `.venv/lib/python3.10/site-packages/tidalapi/`:

- `artist.image(dim)` is the method, `artist.picture` is a string UUID. Valid dims: 160, 320, 480, 750
- `artist.get_radio()` and `artist.get_similar()` take NO args (limit hardcoded)
- `artist.get_top_tracks(limit=None, offset=0)` — None falls back to session default (1000)
- `artist.get_albums(limit=None, offset=0)`, `get_ep_singles()`, `get_other()` — same pattern
- `artist.get_bio()` returns `str`
- `artist.roles` is `Optional[List[Role]]` where Role is an Enum — serialize with `.value`
- `fetch_all_paginated` passes `limit=` and `offset=` as kwargs — tidalapi methods can be passed directly

## Next Steps

1. Merge PR #5 (Phase 1)
2. Start Phase 2: Album & Track Details (`feature/album-track-details`)
   - Flask: `/api/albums/<id>`, `/api/albums/<id>/tracks`, `/api/albums/<id>/similar`, `/api/albums/<id>/review`, `/api/tracks/<id>`, `/api/tracks/<id>/lyrics`
   - MCP: `get_album_info`, `get_album_tracks`, `get_similar_albums`, `get_album_review`, `get_track_info`, `get_track_lyrics`
   - Before implementing, verify `album.similar()`, `album.review()`, `track.lyrics()` signatures against installed tidalapi source

## Test Count by Phase

- Phase 0 (modularization): 111 tests
- Phase 1 (artists): +31 = 142 tests
- Phase 2 (albums/tracks): ~+38 estimated
