import os
import tempfile
import functools

from flask import Flask, request, jsonify
from pathlib import Path

from browser_session import BrowserSession
from utils import (
    format_track_data,
    format_artist_data,
    format_album_data,
    format_playlist_search_data,
    format_video_data,
    format_user_playlist_data,
    bound_limit,
    handle_endpoint_errors,
    safe_attr,
    get_playlist_or_404,
    require_json_body,
    check_user_playlist,
)

app = Flask(__name__)
token_path = os.path.join(tempfile.gettempdir(), 'tidal-session-oauth.json')
SESSION_FILE = Path(token_path)

def requires_tidal_auth(f):
    """
    Decorator to ensure routes have an authenticated TIDAL session.
    Returns 401 if not authenticated.
    Passes the authenticated session to the decorated function.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not SESSION_FILE.exists():
            return jsonify({"error": "Not authenticated"}), 401
        
        # Create session and load from file
        session = BrowserSession()
        login_success = session.login_session_file_auto(SESSION_FILE)
        
        if not login_success:
            return jsonify({"error": "Authentication failed"}), 401
            
        # Add the authenticated session to kwargs
        kwargs['session'] = session
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/auth/login', methods=['GET'])
def login():
    """
    Initiates the TIDAL authentication process.
    Automatically opens a browser for the user to login to their TIDAL account.
    """
    # Create our custom session object
    session = BrowserSession()
    
    def log_message(msg):
        print(f"TIDAL AUTH: {msg}")
    
    # Try to authenticate (will open browser if needed)
    try:
        login_success = session.login_session_file_auto(SESSION_FILE, fn_print=log_message)
        
        if login_success:
            return jsonify({
                "status": "success", 
                "message": "Successfully authenticated with TIDAL",
                "user_id": session.user.id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Authentication failed"
            }), 401
    
    except TimeoutError:
        return jsonify({
            "status": "error",
            "message": "Authentication timed out"
        }), 408
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """
    Check if there's an active authenticated session.
    """
    if not SESSION_FILE.exists():
        return jsonify({
            "authenticated": False,
            "message": "No session file found"
        })
    
    # Create session and try to load from file
    session = BrowserSession()
    login_success = session.login_session_file_auto(SESSION_FILE)
    
    if login_success:
        # Get basic user info
        user_info = {
            "id": session.user.id,
            "username": session.user.username if hasattr(session.user, 'username') else "N/A",
            "email": session.user.email if hasattr(session.user, 'email') else "N/A"            
        }
        
        return jsonify({
            "authenticated": True,
            "message": "Valid TIDAL session",
            "user": user_info
        })
    else:
        return jsonify({
            "authenticated": False,
            "message": "Invalid or expired session"
        })

@app.route('/api/tracks', methods=['GET'])
@requires_tidal_auth
@handle_endpoint_errors("fetching tracks")
def get_tracks(session: BrowserSession):
    """
    Get tracks from the user's history.
    """
    # TODO: Add streaming history support if TIDAL API allows it
    # Get user favorites or history (for now limiting to user favorites only)
    favorites = session.user.favorites

    # Get limit from query parameter, default to 10 if not specified
    limit = bound_limit(request.args.get('limit', default=10, type=int))

    tracks = favorites.tracks(limit=limit, order="DATE", order_direction="DESC")
    track_list = [format_track_data(track) for track in tracks]

    return jsonify({"tracks": track_list})
    
    
@app.route('/api/recommendations/track/<track_id>', methods=['GET'])
@requires_tidal_auth
@handle_endpoint_errors("fetching recommendations")
def get_track_recommendations(track_id: str, session: BrowserSession):
    """
    Get recommended tracks based on a specific track using TIDAL's track radio feature.
    """
    # Get limit from query parameter, default to 10 if not specified
    limit = bound_limit(request.args.get('limit', default=10, type=int))

    # Get recommendations using track radio
    track = session.track(track_id)
    if not track:
        return jsonify({"error": f"Track with ID {track_id} not found"}), 404

    recommendations = track.get_track_radio(limit=limit)

    # Format track data
    track_list = [format_track_data(t) for t in recommendations]
    return jsonify({"recommendations": track_list})    


@app.route('/api/recommendations/batch', methods=['POST'])
@requires_tidal_auth
@handle_endpoint_errors("fetching batch recommendations")
def get_batch_recommendations(session: BrowserSession):
    """
    Get recommended tracks based on a list of track IDs using concurrent requests.
    """
    import concurrent.futures

    data, error = require_json_body(required_fields=['track_ids'])
    if error:
        return error

    track_ids = data['track_ids']
    if not isinstance(track_ids, list):
        return jsonify({"error": "track_ids must be a list"}), 400

    limit_per_track = bound_limit(data.get('limit_per_track', 20))
    remove_duplicates = data.get('remove_duplicates', True)

    def get_single_track_recommendations(tid):
        """Function to get recommendations for a single track"""
        try:
            track = session.track(tid)
            recommendations = track.get_track_radio(limit=limit_per_track)
            # Format track data immediately
            return [
                format_track_data(rec, source_track_id=tid)
                for rec in recommendations
            ]
        except Exception as e:
            print(f"Error getting recommendations for track {tid}: {str(e)}")
            return []

    all_recommendations = []
    seen_track_ids = set()

    # Use ThreadPoolExecutor to process tracks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(track_ids)) as executor:
        # Submit all tasks and map them to their track_ids
        future_to_track_id = {
            executor.submit(get_single_track_recommendations, tid): tid
            for tid in track_ids
        }

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_track_id):
            track_recommendations = future.result()

            # Add recommendations to the result list
            for track_data in track_recommendations:
                tid = track_data.get('id')

                # Skip if we've already seen this track and want to remove duplicates
                if remove_duplicates and tid in seen_track_ids:
                    continue

                all_recommendations.append(track_data)
                seen_track_ids.add(tid)

    return jsonify({"recommendations": all_recommendations})


@app.route('/api/playlists', methods=['POST'])
@requires_tidal_auth
@handle_endpoint_errors("creating playlist")
def create_playlist(session: BrowserSession):
    """
    Creates a new TIDAL playlist and adds tracks to it.

    Expected JSON payload:
    {
        "title": "Playlist title",
        "description": "Playlist description",
        "track_ids": [123456789, 987654321, ...]
    }

    Returns the created playlist information.
    """
    data, error = require_json_body(required_fields=['title', 'track_ids'])
    if error:
        return error

    title = data['title']
    track_ids = data['track_ids']
    description = data.get('description', '')

    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    playlist = session.user.create_playlist(title, description)
    playlist.add(track_ids)
    playlist_info = format_user_playlist_data(playlist)

    return jsonify({
        "status": "success",
        "message": f"Playlist '{title}' created successfully with {len(track_ids)} tracks",
        "playlist": playlist_info
    })


@app.route('/api/playlists', methods=['GET'])
@requires_tidal_auth
@handle_endpoint_errors("fetching playlists")
def get_user_playlists(session: BrowserSession):
    """
    Get the user's playlists from TIDAL.
    """
    # Get user playlists
    playlists = session.user.playlists()

    # Format playlist data using helper
    playlist_list = [format_user_playlist_data(playlist) for playlist in playlists]

    # Sort playlists by last_updated in descending order
    sorted_playlists = sorted(
        playlist_list,
        key=lambda x: x.get('last_updated', ''),
        reverse=True
    )

    return jsonify({"playlists": sorted_playlists})
    

@app.route('/api/playlists/<playlist_id>/tracks', methods=['GET'])
@requires_tidal_auth
@handle_endpoint_errors("fetching playlist tracks")
def get_playlist_tracks(playlist_id: str, session: BrowserSession):
    """
    Get tracks from a specific TIDAL playlist.
    """
    limit = bound_limit(request.args.get('limit', default=100, type=int))

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    tracks = playlist.items(limit=limit)
    track_list = [format_track_data(track) for track in tracks]

    return jsonify({
        "playlist_id": playlist.id,
        "tracks": track_list,
        "total_tracks": len(track_list)
    })
    

@app.route('/api/playlists/<playlist_id>', methods=['DELETE'])
@requires_tidal_auth
@handle_endpoint_errors("deleting playlist")
def delete_playlist(playlist_id: str, session: BrowserSession):
    """
    Delete a TIDAL playlist by its ID.
    """
    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    playlist.delete()

    return jsonify({
        "status": "success",
        "message": f"Playlist with ID {playlist_id} was successfully deleted"
    })


@app.route('/api/search', methods=['GET'])
@requires_tidal_auth
@handle_endpoint_errors("searching")
def search(session: BrowserSession):
    """
    Search TIDAL catalog for artists, tracks, albums, playlists, and videos.

    Query params:
        query: Search query string (required)
        types: Comma-separated list of content types (artists,tracks,albums,playlists,videos)
        limit: Maximum results per type (default: 20, max: 50)
    """
    import tidalapi

    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # Parse types (comma-separated)
    types_param = request.args.get('types', '')
    limit = bound_limit(request.args.get('limit', default=20, type=int))

    # Map type strings to tidalapi models
    type_map = {
        'artists': tidalapi.Artist,
        'tracks': tidalapi.Track,
        'albums': tidalapi.Album,
        'playlists': tidalapi.Playlist,
        'videos': tidalapi.Video
    }

    models = None
    if types_param:
        types_list = [t.strip().lower() for t in types_param.split(',')]
        models = [type_map[t] for t in types_list if t in type_map]
        if not models:
            models = None  # Fall back to searching all if no valid types

    results = session.search(query, models=models, limit=limit)

    # Format results
    response = {
        "query": query,
        "artists": [format_artist_data(a) for a in results.artists] if results.artists else [],
        "tracks": [format_track_data(t) for t in results.tracks] if results.tracks else [],
        "albums": [format_album_data(a) for a in results.albums] if results.albums else [],
        "playlists": [format_playlist_search_data(p) for p in results.playlists] if results.playlists else [],
        "videos": [format_video_data(v) for v in results.videos] if results.videos else [],
    }

    # Include top hit if available
    if results.top_hit:
        top_hit = results.top_hit
        top_hit_type = type(top_hit).__name__.lower()
        if top_hit_type == 'artist':
            response["top_hit"] = {"type": "artist", "data": format_artist_data(top_hit)}
        elif top_hit_type == 'track':
            response["top_hit"] = {"type": "track", "data": format_track_data(top_hit)}
        elif top_hit_type == 'album':
            response["top_hit"] = {"type": "album", "data": format_album_data(top_hit)}
        elif top_hit_type == 'playlist':
            response["top_hit"] = {"type": "playlist", "data": format_playlist_search_data(top_hit)}
        elif top_hit_type == 'video':
            response["top_hit"] = {"type": "video", "data": format_video_data(top_hit)}

    return jsonify(response)


@app.route('/api/playlists/<playlist_id>/tracks', methods=['POST'])
@requires_tidal_auth
@handle_endpoint_errors("adding tracks to playlist")
def add_tracks_to_playlist(playlist_id: str, session: BrowserSession):
    """
    Add tracks to an existing TIDAL playlist.

    Expected JSON payload:
    {
        "track_ids": [123456789, 987654321, ...],
        "allow_duplicates": false,  // optional, default false
        "position": -1  // optional, -1 = append to end
    }
    """
    data, error = require_json_body(required_fields=['track_ids'])
    if error:
        return error

    track_ids = data['track_ids']
    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    allow_duplicates = data.get('allow_duplicates', False)
    position = data.get('position', -1)

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "add")
    if error:
        return error

    if position == -1:
        added_indices = playlist.add(track_ids, allow_duplicates=allow_duplicates)
    else:
        added_indices = playlist.add(track_ids, allow_duplicates=allow_duplicates, position=position)

    return jsonify({
        "status": "success",
        "message": f"Added {len(track_ids)} tracks to playlist",
        "playlist_id": playlist_id,
        "added_count": len(added_indices) if added_indices else len(track_ids)
    })


@app.route('/api/playlists/<playlist_id>/tracks', methods=['DELETE'])
@requires_tidal_auth
@handle_endpoint_errors("removing tracks from playlist")
def remove_tracks_from_playlist(playlist_id: str, session: BrowserSession):
    """
    Remove tracks from a TIDAL playlist.

    Expected JSON payload:
    {
        "track_ids": [123456789, 987654321, ...]
    }
    """
    data, error = require_json_body(required_fields=['track_ids'])
    if error:
        return error

    track_ids = data['track_ids']
    if not isinstance(track_ids, list):
        return jsonify({"error": "'track_ids' must be a list"}), 400

    playlist, error = get_playlist_or_404(session, playlist_id)
    if error:
        return error

    error = check_user_playlist(playlist, "remove")
    if error:
        return error

    removed_count = 0
    for track_id in track_ids:
        try:
            playlist.remove_by_id(track_id)
            removed_count += 1
        except Exception:
            pass

    return jsonify({
        "status": "success",
        "message": f"Removed {removed_count} tracks from playlist",
        "playlist_id": playlist_id,
        "removed_count": removed_count
    })


if __name__ == '__main__':
    import os
    
    # Get port from environment variable or use default
    port = int(os.environ.get("TIDAL_MCP_PORT", 5050))
    
    print(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)