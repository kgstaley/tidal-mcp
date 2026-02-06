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

    def add(self, track_ids, allow_duplicates=False, position=-1):
        return list(range(len(track_ids)))

    def remove_by_id(self, track_id):
        pass


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


class MockResponse:
    """Mock requests.Response object for MCP tool tests."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data
