def format_track_data(track, source_track_id=None):
    """
    Format a track object into a standardized dictionary.
    
    Args:
        track: TIDAL track object
        source_track_id: Optional ID of the track that led to this recommendation
        
    Returns:
        Dictionary with standardized track information
    """
    track_data = {
        "id": track.id,
        "title": track.name,
        "artist": track.artist.name if hasattr(track.artist, 'name') else "Unknown",
        "album": track.album.name if hasattr(track.album, 'name') else "Unknown",
        "duration": track.duration if hasattr(track, 'duration') else 0,
        "url": f"https://tidal.com/browse/track/{track.id}?u"
    }
    
    # Include source track ID if provided
    if source_track_id:
        track_data["source_track_id"] = source_track_id
        
    return track_data

def bound_limit(limit: int, max_n: int = 5000) -> int:
    # Ensure limit is within reasonable bounds
    if limit < 1:
        limit = 1
    elif limit > max_n:
        limit = max_n
    return limit


def fetch_all_paginated(fetch_fn, limit: int, page_size: int = 50) -> list:
    """
    Fetch items with pagination, batching requests until limit is reached.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of items
        limit: Total number of items to fetch
        page_size: Number of items per request (default 50, TIDAL's limit)

    Returns:
        List of all fetched items up to the limit
    """
    all_items = []
    offset = 0

    while len(all_items) < limit:
        batch_limit = min(page_size, limit - len(all_items))
        batch = fetch_fn(limit=batch_limit, offset=offset)

        if not batch:
            break

        all_items.extend(batch)

        if len(batch) < batch_limit:
            break

        offset += len(batch)

    return all_items[:limit]
