"""Shared mock classes and fixtures for all tests."""


class MockArtist:
    """Mock TIDAL artist object."""

    def __init__(self, id=123, name="Test Artist"):
        self.id = id
        self.name = name
        self.roles = []

    def image(self, dimensions=320):
        return f"https://tidal.com/image/{self.id}/{dimensions}x{dimensions}"

    def get_bio(self):
        return None

    def get_top_tracks(self, limit=None, offset=0):
        return []

    def get_albums(self, limit=None, offset=0):
        return []

    def get_ep_singles(self, limit=None, offset=0):
        return []

    def get_other(self, limit=None, offset=0):
        return []

    def get_similar(self):
        return []

    def get_radio(self):
        return []


class MockAlbum:
    """Mock TIDAL album object."""

    def __init__(self, id=456, name="Test Album", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.release_date = "2024-01-15"
        self.num_tracks = 12
        self.duration = 3600
        self.version = None
        self.explicit = False
        self.copyright = "2024 Test Records"
        self.audio_quality = "LOSSLESS"
        self.audio_modes = ["STEREO"]
        self.popularity = 75
        self.tidal_release_date = "2024-01-10"

    def image(self, size):
        return f"https://tidal.com/image/{self.id}/{size}"

    def tracks(self, limit=None, offset=0):
        return []

    def similar(self):
        return []

    def review(self):
        return "A great album."


class MockTrack:
    """Mock TIDAL track object."""

    def __init__(self, id=789, name="Test Track", artist=None, album=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.album = album or MockAlbum()
        self.duration = 240
        self.isrc = "USRC12345678"
        self.explicit = False
        self.track_num = 1
        self.volume_num = 1
        self.version = None
        self.audio_quality = "LOSSLESS"
        self.audio_modes = ["STEREO"]
        self.copyright = "2024 Test Records"
        self.popularity = 80
        self.tidal_release_date = "2024-01-10"

    def lyrics(self):
        return MockLyrics()


class MockLyrics:
    """Mock TIDAL Lyrics object."""

    def __init__(self, text="Test lyrics text", subtitles="", provider="Musixmatch"):
        self.text = text
        self.subtitles = subtitles
        self.provider = provider


class MockCreator:
    """Mock playlist creator."""

    def __init__(self, name="Test User"):
        self.name = name


class MockPlaylist:
    """Mock TIDAL playlist object (with modification capabilities)."""

    def __init__(self, id="abc-123", name="Test Playlist", creator=None):
        self.id = id
        self.name = name
        self.creator = creator or MockCreator()
        self.num_tracks = 25
        self.duration = 5400
        self._tracks = []
        self.public = False

    def add(self, track_ids, allow_duplicates=False, position=-1):
        return list(range(len(track_ids)))

    def remove_by_id(self, track_id):
        pass

    def edit(self, title=None, description=None):
        """Edit playlist metadata."""
        if title:
            self.name = title
        if description:
            self.description = description
        return True

    def move_by_indices(self, indices, position):
        """Move multiple tracks by indices to position."""
        return True

    def clear(self, chunk_size=50):
        """Clear all tracks from playlist."""
        self.num_tracks = 0
        return True

    def merge(self, playlist, allow_duplicates=False, allow_missing=True):
        """Merge tracks from another playlist."""
        return list(range(10))  # Return 10 added indices

    def set_playlist_public(self):
        """Make playlist public."""
        self.public = True
        return True

    def set_playlist_private(self):
        """Make playlist private."""
        self.public = False
        return True


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
        self.public = False

    def edit(self, title=None, description=None):
        """Edit playlist metadata."""
        if title:
            self.name = title
        if description:
            self.description = description
        return True

    def move_by_index(self, index, position):
        """Move track by index to position."""
        return True

    def move_by_indices(self, indices, position):
        """Move multiple tracks by indices to position."""
        return True

    def move_by_id(self, media_id, position):
        """Move track by ID to position."""
        return True

    def clear(self, chunk_size=50):
        """Clear all tracks from playlist."""
        self.num_tracks = 0
        return True

    def merge(self, playlist, allow_duplicates=False, allow_missing=True):
        """Merge tracks from another playlist."""
        return list(range(10))  # Return 10 added indices

    def set_playlist_public(self):
        """Make playlist public."""
        self.public = True
        return True

    def set_playlist_private(self):
        """Make playlist private."""
        self.public = False
        return True


class MockVideo:
    """Mock TIDAL video object."""

    def __init__(self, id=999, name="Test Video", artist=None):
        self.id = id
        self.name = name
        self.artist = artist or MockArtist()
        self.duration = 300


class MockMix:
    """Mock TIDAL mix object."""

    def __init__(
        self,
        id="mix-123",
        title="My Daily Mix",
        sub_title="Daily Mix",
        short_subtitle="Your personalized playlist",
        mix_type="DAILY_MIX",
        updated="2024-01-15T12:00:00",
    ):
        self.id = id
        self.title = title
        self.sub_title = sub_title
        self.short_subtitle = short_subtitle
        self.mix_type = mix_type
        self.updated = updated

    def image(self, dimensions=640):
        return f"https://tidal.com/image/{self.id}/{dimensions}x{dimensions}"

    def items(self):
        return []


class MockPageLink:
    """Mock TIDAL PageLink object."""

    def __init__(self, title="Chill", api_path="pages/moods_chill", icon="mood", image_id="img-chill-123"):
        self.title = title
        self.api_path = api_path
        self.icon = icon
        self.image_id = image_id

    def get(self):
        return MockPage(title=self.title)


class MockPageItem:
    """Mock TIDAL PageItem (featured item) object."""

    def __init__(
        self,
        header="Featured Album",
        short_header="Featured",
        short_sub_header="New Release",
        type="ALBUM",
        artifact_id="album-456",
        featured=True,
    ):
        self.header = header
        self.short_header = short_header
        self.short_sub_header = short_sub_header
        self.type = type
        self.artifact_id = artifact_id
        self.featured = featured
        self.text = ""
        self.image_id = ""


class MockPageCategory:
    """Mock TIDAL PageCategory object."""

    def __init__(self, title="Top Albums", items=None):
        self.title = title
        self.items = items or []
        self.type = None
        self.description = ""


class MockPage:
    """Mock TIDAL Page object."""

    def __init__(self, title="For You", categories=None):
        self.title = title
        self.categories = categories

    def get(self, endpoint, params=None):
        return self


class MockGenre:
    """Mock TIDAL Genre object."""

    def __init__(
        self,
        name="Pop",
        path="pop",
        has_playlists=True,
        has_artists=True,
        has_albums=True,
        has_tracks=True,
        has_videos=False,
        image="pop-image-id",
    ):
        self.name = name
        self.path = path
        self.playlists = has_playlists
        self.artists = has_artists
        self.albums = has_albums
        self.tracks = has_tracks
        self.videos = has_videos
        self.image = image

    def items(self, model):
        return []


class MockResponse:
    """Mock requests.Response object for MCP tool tests."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data
