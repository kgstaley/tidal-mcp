"""Tests for tidal_api/utils.py"""
import sys
from pathlib import Path

# Add tidal_api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tidal_api"))

from utils import bound_limit, fetch_all_paginated


class TestBoundLimit:
    """Tests for the bound_limit function."""

    def test_bound_limit_within_bounds(self):
        """Test limit within valid bounds is unchanged."""
        assert bound_limit(25) == 25
        assert bound_limit(50) == 50
        assert bound_limit(1) == 1

    def test_bound_limit_below_minimum(self):
        """Test limit below 1 is clamped to 1."""
        assert bound_limit(0) == 1
        assert bound_limit(-5) == 1
        assert bound_limit(-100) == 1

    def test_bound_limit_above_maximum_default(self):
        """Test limit above default max (5000) is clamped."""
        assert bound_limit(5001) == 5000
        assert bound_limit(10000) == 5000

    def test_bound_limit_custom_max(self):
        """Test limit with custom max_n value."""
        assert bound_limit(100, max_n=50) == 50
        assert bound_limit(25, max_n=50) == 25
        assert bound_limit(200, max_n=100) == 100

    def test_bound_limit_edge_cases(self):
        """Test edge cases for bound_limit."""
        # Exactly at the max
        assert bound_limit(5000) == 5000
        assert bound_limit(50, max_n=50) == 50


class TestFetchAllPaginated:
    """Tests for the fetch_all_paginated function."""

    def test_single_batch_exact_count(self):
        """Test fetching when all items fit in a single batch."""
        items = list(range(30))

        def fetch_fn(limit, offset):
            return items[offset:offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=30, page_size=50)
        assert result == list(range(30))
        assert len(result) == 30

    def test_multiple_batches(self):
        """Test fetching across multiple batches."""
        items = list(range(120))

        def fetch_fn(limit, offset):
            return items[offset:offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=120, page_size=50)
        assert result == list(range(120))
        assert len(result) == 120

    def test_limit_less_than_page_size(self):
        """Test fetching when limit is less than page_size."""
        items = list(range(100))

        def fetch_fn(limit, offset):
            return items[offset:offset + limit]

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
            return items[offset:offset + limit]

        result = fetch_all_paginated(fetch_fn, limit=75, page_size=50)
        assert result == list(range(75))
        assert len(result) == 75

    def test_stops_when_source_exhausted(self):
        """Test that fetching stops when source is exhausted before limit is reached."""
        items = list(range(30))

        def fetch_fn(limit, offset):
            return items[offset:offset + limit]

        # Requesting 100 but only 30 available
        result = fetch_all_paginated(fetch_fn, limit=100, page_size=50)
        assert result == list(range(30))
        assert len(result) == 30

    def test_custom_page_size(self):
        """Test fetching with custom page size."""
        items = list(range(100))

        def fetch_fn(limit, offset):
            return items[offset:offset + limit]

        # Use page_size of 25
        result = fetch_all_paginated(fetch_fn, limit=100, page_size=25)
        assert result == list(range(100))
        assert len(result) == 100

    def test_limits_result_to_requested_count(self):
        """Test that result is truncated to requested limit."""
        items = list(range(200))

        def fetch_fn(limit, offset):
            # Simulate API returning more than requested
            return items[offset:offset + limit + 5]

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
            return items[offset:offset + limit]

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
