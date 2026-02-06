"""Unit tests for tidal_api/utils.py"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project paths for imports - must be first before any other imports
tidal_api_path = str(Path(__file__).parent.parent / "tidal_api")
if tidal_api_path not in sys.path:
    sys.path.insert(0, tidal_api_path)

# Import directly from the file to avoid module caching issues
import importlib.util

spec = importlib.util.spec_from_file_location("tidal_utils", Path(__file__).parent.parent / "tidal_api" / "utils.py")
tidal_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tidal_utils)

format_track_data = tidal_utils.format_track_data
format_artist_data = tidal_utils.format_artist_data
format_album_data = tidal_utils.format_album_data
format_playlist_search_data = tidal_utils.format_playlist_search_data
format_video_data = tidal_utils.format_video_data
format_user_playlist_data = tidal_utils.format_user_playlist_data
bound_limit = tidal_utils.bound_limit
fetch_all_paginated = tidal_utils.fetch_all_paginated
safe_attr = tidal_utils.safe_attr
handle_endpoint_errors = tidal_utils.handle_endpoint_errors
tidal_track_url = tidal_utils.tidal_track_url
tidal_artist_url = tidal_utils.tidal_artist_url
tidal_album_url = tidal_utils.tidal_album_url
tidal_playlist_url = tidal_utils.tidal_playlist_url
tidal_video_url = tidal_utils.tidal_video_url
get_playlist_or_404 = tidal_utils.get_playlist_or_404
require_json_body = tidal_utils.require_json_body
check_user_playlist = tidal_utils.check_user_playlist


class MockArtist:
    """Mock TIDAL artist object."""

    def __init__(self, id=123, name="Test Artist"):
        self.id = id
        self.name = name

    def picture(self, size):
        return f"https://tidal.com/picture/{self.id}/{size}"


class MockAlbum:
    """Mock TIDAL album object."""

    def __init__(self, id=456, name="Test Album", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.release_date = "2024-01-15"
        self.num_tracks = 12
        self.duration = 3600

    def image(self, size):
        return f"https://tidal.com/image/{self.id}/{size}"


class MockTrack:
    """Mock TIDAL track object."""

    def __init__(self, id=789, name="Test Track", artist=None, album=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.album = album or MockAlbum()
        self.duration = 240


class MockCreator:
    """Mock playlist creator."""

    def __init__(self, name="Test User"):
        self.name = name


class MockPlaylist:
    """Mock TIDAL playlist object."""

    def __init__(self, id="abc-123", name="Test Playlist", creator=None):
        self.id = id
        self.name = name
        self.creator = creator or MockCreator()
        self.num_tracks = 25
        self.duration = 5400


class MockUserPlaylist:
    """Mock TIDAL user playlist object (for format_user_playlist_data)."""

    def __init__(self, id="user-playlist-123", name="My Playlist"):
        self.id = id
        self.name = name
        self.description = "A test playlist"
        self.created = "2024-01-01T00:00:00"
        self.last_updated = "2024-06-15T12:00:00"
        self.num_tracks = 42
        self.duration = 7200


class MockVideo:
    """Mock TIDAL video object."""

    def __init__(self, id=999, name="Test Video", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.duration = 300


class TestFormatTrackData:
    """Tests for format_track_data function."""

    def test_basic_track_formatting(self):
        track = MockTrack()
        result = format_track_data(track)

        assert result["id"] == 789
        assert result["title"] == "Test Track"
        assert result["artist"] == "Test Artist"
        assert result["album"] == "Test Album"
        assert result["duration"] == 240
        assert "tidal.com/browse/track/789" in result["url"]

    def test_track_with_source_id(self):
        track = MockTrack()
        result = format_track_data(track, source_track_id="source-123")

        assert result["source_track_id"] == "source-123"

    def test_track_without_source_id(self):
        track = MockTrack()
        result = format_track_data(track)

        assert "source_track_id" not in result


class TestFormatArtistData:
    """Tests for format_artist_data function."""

    def test_basic_artist_formatting(self):
        artist = MockArtist(id=100, name="Famous Artist")
        result = format_artist_data(artist)

        assert result["id"] == 100
        assert result["name"] == "Famous Artist"
        assert "tidal.com/browse/artist/100" in result["url"]
        assert result["picture_url"] is not None

    def test_artist_picture_url(self):
        artist = MockArtist(id=200)
        result = format_artist_data(artist)

        assert "200" in result["picture_url"]
        assert "640" in result["picture_url"]


class TestFormatAlbumData:
    """Tests for format_album_data function."""

    def test_basic_album_formatting(self):
        artist = MockArtist(name="Album Artist")
        album = MockAlbum(id=300, name="Great Album", artist=artist)
        result = format_album_data(album)

        assert result["id"] == 300
        assert result["name"] == "Great Album"
        assert result["artist"] == "Album Artist"
        assert result["release_date"] == "2024-01-15"
        assert result["num_tracks"] == 12
        assert result["duration"] == 3600
        assert "tidal.com/browse/album/300" in result["url"]

    def test_album_cover_url(self):
        album = MockAlbum(id=400)
        result = format_album_data(album)

        assert result["cover_url"] is not None
        assert "400" in result["cover_url"]


class TestFormatPlaylistSearchData:
    """Tests for format_playlist_search_data function."""

    def test_basic_playlist_formatting(self):
        creator = MockCreator(name="Playlist Creator")
        playlist = MockPlaylist(id="playlist-123", name="My Playlist", creator=creator)
        result = format_playlist_search_data(playlist)

        assert result["id"] == "playlist-123"
        assert result["title"] == "My Playlist"
        assert result["creator"] == "Playlist Creator"
        assert result["track_count"] == 25
        assert result["duration"] == 5400
        assert "tidal.com/playlist/playlist-123" in result["url"]

    def test_playlist_without_creator(self):
        playlist = MockPlaylist(id="playlist-456")
        playlist.creator = None
        result = format_playlist_search_data(playlist)

        assert result["creator"] is None


class TestFormatVideoData:
    """Tests for format_video_data function."""

    def test_basic_video_formatting(self):
        artist = MockArtist(name="Video Artist")
        video = MockVideo(id=500, name="Music Video", artist=artist)
        result = format_video_data(video)

        assert result["id"] == 500
        assert result["title"] == "Music Video"
        assert result["artist"] == "Video Artist"
        assert result["duration"] == 300
        assert "tidal.com/browse/video/500" in result["url"]


class TestBoundLimit:
    """Tests for bound_limit function."""

    def test_normal_limit(self):
        assert bound_limit(25) == 25
        assert bound_limit(10) == 10

    def test_limit_below_minimum(self):
        assert bound_limit(0) == 1
        assert bound_limit(-5) == 1
        assert bound_limit(-100) == 1

    def test_limit_above_maximum_default(self):
        """Test limit above default max (5000) is clamped."""
        assert bound_limit(5001) == 5000
        assert bound_limit(10000) == 5000

    def test_custom_max_limit(self):
        assert bound_limit(100, max_n=200) == 100
        assert bound_limit(300, max_n=200) == 200
        assert bound_limit(100, max_n=50) == 50

    def test_boundary_values(self):
        assert bound_limit(1) == 1
        assert bound_limit(5000) == 5000
        assert bound_limit(50, max_n=50) == 50


class TestFetchAllPaginated:
    """Tests for the fetch_all_paginated function."""

    def test_single_batch_exact_count(self):
        """Test fetching when all items fit in a single batch."""
        items = list(range(30))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=30, page_size=50)
        assert result == list(range(30))
        assert len(result) == 30

    def test_multiple_batches(self):
        """Test fetching across multiple batches."""
        items = list(range(120))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=120, page_size=50)
        assert result == list(range(120))
        assert len(result) == 120

    def test_limit_less_than_page_size(self):
        """Test fetching when limit is less than page_size."""
        items = list(range(100))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=25, page_size=50)
        assert result == list(range(25))
        assert len(result) == 25

    def test_empty_result(self):
        """Test fetching when source has no items."""

        def fetch_fn(limit, offset):
            return []

        result = fetch_all_paginated(fetch_fn, limit=50, page_size=50)
        assert result == []
        assert len(result) == 0

    def test_partial_last_batch(self):
        """Test fetching when last batch is partial."""
        items = list(range(75))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=75, page_size=50)
        assert result == list(range(75))
        assert len(result) == 75

    def test_stops_when_source_exhausted(self):
        """Test that fetching stops when source is exhausted before limit is reached."""
        items = list(range(30))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        # Requesting 100 but only 30 available
        result = fetch_all_paginated(fetch_fn, limit=100, page_size=50)
        assert result == list(range(30))
        assert len(result) == 30

    def test_custom_page_size(self):
        """Test fetching with custom page size."""
        items = list(range(100))

        def fetch_fn(limit, offset):
            return items[offset : offset + limit]

        # Use page_size of 25
        result = fetch_all_paginated(fetch_fn, limit=100, page_size=25)
        assert result == list(range(100))
        assert len(result) == 100

    def test_limits_result_to_requested_count(self):
        """Test that result is truncated to requested limit."""
        items = list(range(200))

        def fetch_fn(limit, offset):
            # Simulate API returning more than requested
            return items[offset : offset + limit + 5]

        result = fetch_all_paginated(fetch_fn, limit=50, page_size=50)
        assert len(result) == 50
        assert result == list(range(50))

    def test_tracks_offset_correctly(self):
        """Test that offsets are tracked correctly across batches."""
        call_log = []

        def fetch_fn(limit, offset):
            call_log.append((limit, offset))
            # Return batch_limit items starting at offset
            return list(range(offset, offset + limit))

        result = fetch_all_paginated(fetch_fn, limit=150, page_size=50)

        # Should have made 3 calls with offsets 0, 50, 100
        assert len(call_log) == 3
        assert call_log[0] == (50, 0)
        assert call_log[1] == (50, 50)
        assert call_log[2] == (50, 100)
        assert len(result) == 150

    def test_batch_limit_adjusted_for_final_batch(self):
        """Test that final batch limit is adjusted when approaching limit."""
        call_log = []
        items = list(range(200))

        def fetch_fn(limit, offset):
            call_log.append((limit, offset))
            return items[offset : offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=75, page_size=50)

        # First call: 50 items, second call: 25 items (to reach 75 total)
        assert len(call_log) == 2
        assert call_log[0] == (50, 0)
        assert call_log[1] == (25, 50)
        assert len(result) == 75

    def test_stops_on_empty_batch(self):
        """Test that fetching stops immediately on empty batch."""
        call_count = [0]

        def fetch_fn(limit, offset):
            call_count[0] += 1
            if offset == 0:
                return list(range(50))
            return []  # Empty batch on second call

        result = fetch_all_paginated(fetch_fn, limit=200, page_size=50)

        assert call_count[0] == 2  # Only 2 calls made
        assert len(result) == 50


class TestFormatUserPlaylistData:
    """Tests for format_user_playlist_data function."""

    def test_basic_user_playlist_formatting(self):
        playlist = MockUserPlaylist()
        result = format_user_playlist_data(playlist)

        assert result["id"] == "user-playlist-123"
        assert result["title"] == "My Playlist"
        assert result["description"] == "A test playlist"
        assert result["created"] == "2024-01-01T00:00:00"
        assert result["last_updated"] == "2024-06-15T12:00:00"
        assert result["track_count"] == 42
        assert result["duration"] == 7200
        assert "tidal.com/playlist/user-playlist-123" in result["url"]

    def test_playlist_with_missing_attributes(self):
        """Test playlist with missing optional attributes."""

        class MinimalPlaylist:
            id = "minimal-123"
            name = "Minimal"

        playlist = MinimalPlaylist()
        result = format_user_playlist_data(playlist)

        assert result["id"] == "minimal-123"
        assert result["title"] == "Minimal"
        assert result["description"] == ""
        assert result["track_count"] == 0
        assert result["duration"] == 0


class TestSafeAttr:
    """Tests for safe_attr function."""

    def test_existing_attribute(self):
        class Obj:
            name = "test"

        assert safe_attr(Obj(), "name") == "test"

    def test_missing_attribute_default(self):
        class Obj:
            pass

        assert safe_attr(Obj(), "name") is None

    def test_missing_attribute_custom_default(self):
        class Obj:
            pass

        assert safe_attr(Obj(), "name", "default") == "default"

    def test_none_attribute(self):
        class Obj:
            name = None

        assert safe_attr(Obj(), "name") is None
        assert safe_attr(Obj(), "name", "default") is None


class TestUrlBuilders:
    """Tests for URL builder functions."""

    def test_tidal_track_url(self):
        url = tidal_track_url(12345)
        assert url == "https://tidal.com/browse/track/12345?u"

    def test_tidal_artist_url(self):
        url = tidal_artist_url(67890)
        assert url == "https://tidal.com/browse/artist/67890"

    def test_tidal_album_url(self):
        url = tidal_album_url(11111)
        assert url == "https://tidal.com/browse/album/11111"

    def test_tidal_playlist_url(self):
        url = tidal_playlist_url("abc-123")
        assert url == "https://tidal.com/playlist/abc-123"

    def test_tidal_video_url(self):
        url = tidal_video_url(99999)
        assert url == "https://tidal.com/browse/video/99999"


class TestHandleEndpointErrors:
    """Tests for handle_endpoint_errors decorator."""

    def test_successful_function(self):
        """Decorator should pass through successful returns."""

        @handle_endpoint_errors("testing")
        def success_func():
            return {"status": "ok"}

        result = success_func()
        assert result == {"status": "ok"}

    def test_exception_caught(self):
        """Decorator should catch exceptions and return error response."""

        @handle_endpoint_errors("testing")
        def failing_func():
            raise ValueError("Something went wrong")

        # jsonify just returns what we pass to it (identity function for testing)
        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "jsonify", mock_jsonify):
            result, status = failing_func()

        # The decorator returns (jsonify({...}), 500)
        assert status == 500
        assert "error" in result
        assert "testing" in result["error"]
        assert "Something went wrong" in result["error"]

    def test_operation_in_error_message(self):
        """Error message should include the operation description."""

        @handle_endpoint_errors("creating playlist")
        def failing_func():
            raise RuntimeError("Network timeout")

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "jsonify", mock_jsonify):
            result, status = failing_func()

        assert "creating playlist" in result["error"]


class TestGetPlaylistOr404:
    """Tests for get_playlist_or_404 function."""

    def test_playlist_found(self):
        """Should return playlist and None error when found."""
        mock_session = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist.id = "test-123"
        mock_session.playlist.return_value = mock_playlist

        playlist, error = get_playlist_or_404(mock_session, "test-123")

        assert playlist == mock_playlist
        assert error is None
        mock_session.playlist.assert_called_once_with("test-123")

    def test_playlist_not_found(self):
        """Should return None and 404 error tuple when not found."""
        mock_session = MagicMock()
        mock_session.playlist.return_value = None

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "jsonify", mock_jsonify):
            playlist, error = get_playlist_or_404(mock_session, "nonexistent-id")

        assert playlist is None
        assert error is not None
        response, status_code = error
        assert status_code == 404
        assert "not found" in response["error"].lower()


class TestRequireJsonBody:
    """Tests for require_json_body function."""

    def test_valid_body_no_required_fields(self):
        """Should return data and None error when body exists."""
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"key": "value"}

        with patch.object(tidal_utils, "request", mock_request):
            data, error = require_json_body()

        assert data == {"key": "value"}
        assert error is None

    def test_valid_body_with_required_fields(self):
        """Should return data when all required fields present."""
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"title": "Test", "track_ids": [1, 2, 3]}

        with patch.object(tidal_utils, "request", mock_request):
            data, error = require_json_body(required_fields=["title", "track_ids"])

        assert error is None
        assert data["title"] == "Test"
        assert data["track_ids"] == [1, 2, 3]

    def test_missing_body(self):
        """Should return None and 400 error when body is missing."""
        mock_request = MagicMock()
        mock_request.get_json.return_value = None

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "request", mock_request):
            with patch.object(tidal_utils, "jsonify", mock_jsonify):
                data, error = require_json_body()

        assert data is None
        assert error is not None
        response, status_code = error
        assert status_code == 400

    def test_missing_required_field(self):
        """Should return None and 400 error when required field is missing."""
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"title": "Test"}

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "request", mock_request):
            with patch.object(tidal_utils, "jsonify", mock_jsonify):
                data, error = require_json_body(required_fields=["title", "track_ids"])

        assert data is None
        assert error is not None
        response, status_code = error
        assert status_code == 400
        assert "track_ids" in response["error"]

    def test_empty_required_list_field(self):
        """Should return None and 400 error when required list field is empty."""
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"title": "Test", "track_ids": []}

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "request", mock_request):
            with patch.object(tidal_utils, "jsonify", mock_jsonify):
                data, error = require_json_body(required_fields=["title", "track_ids"])

        assert data is None
        assert error is not None
        response, status_code = error
        assert status_code == 400


class TestCheckUserPlaylist:
    """Tests for check_user_playlist function."""

    def test_playlist_with_add_capability(self):
        """Should return None when playlist has add method."""
        mock_playlist = MagicMock()
        mock_playlist.add = MagicMock()

        error = check_user_playlist(mock_playlist, "add")

        assert error is None

    def test_playlist_without_add_capability(self):
        """Should return 403 error when playlist lacks add method."""

        class NoAddPlaylist:
            id = "test"
            name = "Test"

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "jsonify", mock_jsonify):
            error = check_user_playlist(NoAddPlaylist(), "add")

        assert error is not None
        response, status_code = error
        assert status_code == 403
        assert "Cannot modify" in response["error"]

    def test_playlist_with_remove_capability(self):
        """Should return None when playlist has remove_by_id method."""
        mock_playlist = MagicMock()
        mock_playlist.remove_by_id = MagicMock()

        error = check_user_playlist(mock_playlist, "remove")

        assert error is None

    def test_playlist_without_remove_capability(self):
        """Should return 403 error when playlist lacks remove_by_id method."""

        class NoRemovePlaylist:
            id = "test"
            name = "Test"

        mock_jsonify = MagicMock(side_effect=lambda x: x)
        with patch.object(tidal_utils, "jsonify", mock_jsonify):
            error = check_user_playlist(NoRemovePlaylist(), "remove")

        assert error is not None
        response, status_code = error
        assert status_code == 403
        assert "Cannot modify" in response["error"]
