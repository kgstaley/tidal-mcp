# Session State — Feature Expansion Plan

Last updated: 2026-02-06

## Current Branch

`main` — All recent PRs merged (Phase 3, Phase 5, patterns documentation)

## Plan File

Full plan: `.claude/plans/clever-twirling-newell.md` (also at `.claude/plans/in-progress/2025-02-05-feature-expansion.md`)

## Phase Status

| Phase | Branch | Status | PR |
|-------|--------|--------|---|
| 0 — Modularize routes/tools | `refactor/modularize-routes-tools` | **Merged** | #4 |
| 1 — Artist deep-dive | `feature/artist-deep-dive` | **Merged** | #5 |
| 2 — Album & track details | `feature/album-track-details` | **Merged** | #8 |
| 3 — Mixes & radio | `feature/mixes-radio` | **Merged** | #9 |
| 4 — Full favorites CRUD | — | **Skipped** | (see note below) |
| 5 — Playlist editing | `feature/playlist-editing` | **Merged** | #11 |
| 6 — Discovery & browsing | — | Not started | — |

## Phase 4 (Skipped) — Full Favorites CRUD

**Status:** Skipped (2026-02-06)

**Original scope:** Comprehensive favorites management across all content types:
- GET/POST/DELETE for `/api/favorites/artists`, `/api/favorites/albums`, `/api/favorites/tracks`
- GET for `/api/favorites/videos`, `/api/favorites/mixes`
- MCP tools: `get_favorites(type)`, `add_favorite(type, id)`, `remove_favorite(type, id)`

**Why skipped:** Project prioritized playlist editing features (Phase 5) for immediate user value. Basic track favorites functionality already exists via `get_favorite_tracks()`. Full favorites CRUD across all content types deferred for future consideration.

**Current favorites support:**
- Tracks: `GET /api/tracks/favorites` + `get_favorite_tracks()` tool (existing since Phase 0)
- Albums, artists, videos, mixes: Read-only access possible via search/browse, but no favorites management

**Future work:** If favorites management becomes a priority, Phase 4 scope can be revisited. Would require:
- 8-10 new Flask endpoints
- 3 unified MCP tools with type parameter
- ~40-50 tests
- Extended mock classes for each content type

## Documentation Updates (PR #10)

Merged 2026-02-06 at 16:38 UTC (between Phase 3 and Phase 5 merges).

**Commit:** `81fc0ae` — Add comprehensive implementation patterns documentation

**Added:**
- `docs/patterns.md` (863 lines) — comprehensive implementation patterns guide with real code examples
- Covers formatters, Flask endpoints, MCP tools, testing, error handling, tidalapi patterns
- All examples extracted from working codebase (artists domain from Phase 1)
- Updated `CLAUDE.md` to reference patterns.md for detailed guidance
- Added patterns.md link to `docs/development.md` Architecture section

**Benefits:**
- Provides working code examples rather than just descriptions
- Documents tidalapi gotchas discovered during Phases 1-3
- Ensures consistency across future feature implementations

## Phase 5 Summary (Playlist Editing)

1 commit on `feature/playlist-editing` (merged as PR #11, 2026-02-06 at 17:10 UTC):

1. `e418bcc` — Add playlist editing features (Phase 5)

### What was added

**Flask endpoints** (`tidal_api/routes/playlists.py`):
- `PATCH /api/playlists/<id>` — edit title/description
- `POST /api/playlists/<id>/visibility/public` — make playlist public
- `POST /api/playlists/<id>/visibility/private` — make playlist private
- `DELETE /api/playlists/<id>/tracks/all` — clear all tracks from playlist
- `POST /api/playlists/<id>/tracks/reorder` — reorder tracks by indices
- `POST /api/playlists/<id>/merge` — merge tracks from another playlist

**MCP tools** (`mcp_server/tools/playlists.py`):
- `edit_tidal_playlist(playlist_id, title=None, description=None)` — edit metadata
- `set_tidal_playlist_visibility(playlist_id, public)` — toggle public/private
- `clear_tidal_playlist(playlist_id, chunk_size=50)` — remove all tracks
- `reorder_tidal_playlist_tracks(playlist_id, indices, position)` — reorder tracks
- `merge_tidal_playlists(target_id, source_id, allow_duplicates, allow_missing)` — merge playlists

**Helpers/formatters** (`mcp_server/utils.py`, `tidal_api/utils.py`):
- `mcp_patch()` — new HTTP helper for PATCH requests (line 252+)
- Extended `check_user_playlist()` to validate new operations (edit, move, clear, merge, visibility)

**Mocks** (`tests/conftest.py`):
- Extended `MockUserPlaylist` with 8 new methods: `edit()`, `set_playlist_public()`, `set_playlist_private()`, `clear()`, `move_by_indices()`, `merge()`, plus `public` attribute
- Extended `MockPlaylist` base class where needed

**Tests**: 191 total (same as Phase 3 — Phase 5 merged without test additions)

### Implementation notes

- Uses RESTful patterns: PATCH for updates, POST for actions, DELETE for removal
- All operations validate user ownership via `check_user_playlist()` before execution
- Merge operation preserves source playlist (non-destructive)
- Clear operation removes tracks in configurable chunks (default 50) for performance
- Reorder uses 0-based indexing matching Python conventions
- All endpoints follow established decorator stack: `@requires_tidal_auth` + `@handle_endpoint_errors()`

### Key tidalapi v0.8.3 learnings (Phase 5)

Verified against installed source at `.venv/lib/python3.10/site-packages/tidalapi/`:
- `playlist.edit(title=None, description=None)` — at least one parameter required
- `playlist.set_playlist_public()` — no args
- `playlist.set_playlist_private()` — no args
- `playlist.clear(chunk_size=50)` — removes all tracks in batches
- `playlist.move_by_indices(indices: List[int], position: int)` — 0-based indexing
- `playlist.merge(other_playlist, allow_duplicates=False, allow_missing=True)` — returns list of added indices
- User playlist operations require UserPlaylist type with `_user` and `_capability` attributes

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

1. ✅ Phase 3 merged (PR #9)
2. ✅ Documentation patterns added (PR #10)
3. ✅ Phase 5 merged (PR #11)
4. **TODO:** Add comprehensive test coverage for Phase 5 playlist editing features (~50 new tests)
5. Consider Phase 6: Discovery & browsing (genres, pages, moods, curated content)
6. Consider Phase 4 (favorites CRUD) if user-requested

## Test Count by Phase

- Phase 0 (modularization): 111 tests
- Phase 1 (artists): +31 = 142 tests
- Phase 2 (albums/tracks): +36 = 178 tests
- Phase 3 (mixes): +13 = 191 tests
- Phase 5 (playlist editing): +0 = 191 tests (implementation only, tests pending)
