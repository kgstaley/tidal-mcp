# Session State — Feature Expansion Plan

Last updated: 2026-02-06

## Current Branch

`feature/mixes-radio` — Phase 3 implementation

## Plan File

Full plan: `.claude/plans/clever-twirling-newell.md` (also at `.claude/plans/in-progress/2025-02-05-feature-expansion.md`)

## Phase Status

| Phase | Branch | Status | PR |
|-------|--------|--------|---|
| 0 — Modularize routes/tools | `refactor/modularize-routes-tools` | **Merged** | #4 |
| 1 — Artist deep-dive | `feature/artist-deep-dive` | **Merged** | #5 |
| 2 — Album & track details | `feature/album-track-details` | **Merged** | #8 |
| 3 — Mixes & radio | `feature/mixes-radio` | **Ready for PR** | — |
| 4 — Full favorites CRUD | — | Not started | — |
| 5 — Playlist enhancements | — | Not started | — |
| 6 — Discovery & browsing | — | Not started | — |

## Phase 3 Summary (Mixes & Radio)

1 commit on `feature/mixes-radio`:

1. Add mixes endpoints and MCP tools (Phase 3)

### What was added

**Flask endpoints** (`tidal_api/routes/mixes.py`):
- `GET /api/mixes` — user's mixes (iterates Page.categories to collect Mix items)
- `GET /api/mixes/<id>/tracks` — tracks in a mix (filters out videos)

**MCP tools** (`mcp_server/tools/mixes.py`):
- `get_user_mixes`, `get_mix_tracks`

**Helpers/formatters** (`tidal_api/utils.py`):
- `format_mix_data()` — id, title, sub_title, short_subtitle, mix_type, image_url, updated

**Mocks** (`tests/conftest.py`):
- New `MockMix` class

**Tests**: 191 total (13 new mix tests: 7 Flask + 6 MCP)

### Key tidalapi v0.8.3 learnings (Phase 3)

- `session.mixes()` → `Page` object with `.categories` (list of categories, each with `.items`)
- `mix.items()` → `List[Track | Video]` — no args, returns mix contents
- `mix.image(dimensions)` — valid dims: 320, 640, 1500
- Mix attrs: `id`, `title`, `sub_title`, `short_subtitle`, `mix_type` (enum), `images`, `content_behaviour`, `updated`

## Phase 2 Summary (Album & Track Details)

1 commit on `feature/album-track-details`:

1. `9f4e045` — Add album detail and track detail endpoints (Phase 2)

### What was added

**Flask endpoints** (`tidal_api/routes/albums.py`):
- `GET /api/albums/<id>` — album info with review, audio quality, popularity
- `GET /api/albums/<id>/tracks` — album tracks (paginated via `fetch_all_paginated`)
- `GET /api/albums/<id>/similar` — similar albums (`album.similar()`, no args)
- `GET /api/albums/<id>/review` — album review (catches HTTPError → 404)
- `GET /api/tracks/<id>` — track detail with ISRC, audio quality, etc.
- `GET /api/tracks/<id>/lyrics` — track lyrics (catches exception → 404)

**MCP tools** (`mcp_server/tools/albums.py`):
- `get_album_info`, `get_album_tracks`, `get_similar_albums`, `get_album_review`, `get_track_info`, `get_track_lyrics`

**Helpers/formatters** (`tidal_api/utils.py`):
- `format_album_detail_data()` — extends base with version, explicit, copyright, audio quality/modes, popularity, tidal_release_date, review
- `format_track_detail_data()` — extends base with isrc, explicit, track_num, volume_num, version, audio quality/modes, copyright, popularity, tidal_release_date
- `format_lyrics_data()` — text, subtitles, provider

**Mocks** (`tests/conftest.py`):
- Extended `MockAlbum` with detail attrs + `tracks()`, `similar()`, `review()` methods
- Extended `MockTrack` with detail attrs + `lyrics()` method
- New `MockLyrics` class

**Tests**: 178 total (36 new album/track tests)

### Key tidalapi v0.8.3 learnings (Phase 2)

Verified against installed source at `.venv/lib/python3.10/site-packages/tidalapi/`:

- `album.tracks(limit=None, offset=0, sparse_album=False)` → `List[Track]`
- `album.similar()` → `List[Album]` — NO params, raises `MetadataNotAvailable` (from `tidalapi.exceptions`)
- `album.review()` → `str` — NO params, raises `requests.HTTPError` if no review
- `album.image(dimensions=320)` — valid dims: 80, 160, 320, 640, 1280
- `track.lyrics()` → `Lyrics` object — NO params, raises `MetadataNotAvailable`
- `Lyrics` class attrs: `track_id`, `provider`, `provider_track_id`, `provider_lyrics_id`, `text`, `subtitles`, `right_to_left`
- Track has NO `image()` method
- Album attrs: `version`, `explicit`, `copyright`, `audio_quality`, `audio_modes`, `popularity`, `tidal_release_date`, `universal_product_number`
- Track attrs (via Media base): `isrc`, `explicit`, `track_num`, `volume_num`, `version`, `audio_quality`, `audio_modes`, `copyright`, `popularity`, `tidal_release_date`

## Phase 1 Summary (Artist Deep-Dive)

3 commits on `feature/artist-deep-dive` (merged as PR #5):

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

**Tests**: 142 total (31 new artist tests)

## Next Steps

1. Open draft PR for Phase 3
2. Start Phase 4: Full favorites CRUD
3. Phases 5-6: Playlist enhancements, Discovery & browsing

## Test Count by Phase

- Phase 0 (modularization): 111 tests
- Phase 1 (artists): +31 = 142 tests
- Phase 2 (albums/tracks): +36 = 178 tests
- Phase 3 (mixes): +13 = 191 tests
