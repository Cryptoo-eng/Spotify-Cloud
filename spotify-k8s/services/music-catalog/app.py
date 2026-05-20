"""
Music Catalog Service - Song, Album, Artist metadata
Mimics Spotify's catalog service that manages millions of tracks
"""

from flask import Flask, request, jsonify
import time
import random
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()

# Simulated Catalog Data
ARTISTS = [
    {"id": "art_001", "name": "The Weeknd", "genres": ["pop", "r&b"], "monthly_listeners": 85000000, "image": "🎤"},
    {"id": "art_002", "name": "Taylor Swift", "genres": ["pop", "country"], "monthly_listeners": 95000000, "image": "🎸"},
    {"id": "art_003", "name": "Drake", "genres": ["hip-hop", "rap"], "monthly_listeners": 78000000, "image": "🎵"},
    {"id": "art_004", "name": "Billie Eilish", "genres": ["alternative", "pop"], "monthly_listeners": 72000000, "image": "🎙️"},
    {"id": "art_005", "name": "Ed Sheeran", "genres": ["pop", "acoustic"], "monthly_listeners": 88000000, "image": "🎻"},
    {"id": "art_006", "name": "Ariana Grande", "genres": ["pop", "r&b"], "monthly_listeners": 83000000, "image": "🎤"},
    {"id": "art_007", "name": "Post Malone", "genres": ["hip-hop", "pop"], "monthly_listeners": 65000000, "image": "🎙️"},
    {"id": "art_008", "name": "Dua Lipa", "genres": ["pop", "dance"], "monthly_listeners": 71000000, "image": "🎵"},
]

ALBUMS = [
    {"id": "alb_001", "title": "After Hours", "artist_id": "art_001", "year": 2020, "tracks": 14, "cover": "🌙"},
    {"id": "alb_002", "title": "Midnights", "artist_id": "art_002", "year": 2022, "tracks": 13, "cover": "⭐"},
    {"id": "alb_003", "title": "Certified Lover Boy", "artist_id": "art_003", "year": 2021, "tracks": 21, "cover": "💚"},
    {"id": "alb_004", "title": "Happier Than Ever", "artist_id": "art_004", "year": 2021, "tracks": 16, "cover": "🌊"},
    {"id": "alb_005", "title": "Equals", "artist_id": "art_005", "year": 2021, "tracks": 14, "cover": "➕"},
    {"id": "alb_006", "title": "Positions", "artist_id": "art_006", "year": 2020, "tracks": 14, "cover": "♾️"},
    {"id": "alb_007", "title": "Hollywood's Bleeding", "artist_id": "art_007", "year": 2019, "tracks": 17, "cover": "🩸"},
    {"id": "alb_008", "title": "Future Nostalgia", "artist_id": "art_008", "year": 2020, "tracks": 11, "cover": "🕺"},
]

TRACKS = [
    {"id": "trk_001", "title": "Blinding Lights", "artist_id": "art_001", "album_id": "alb_001", "duration_ms": 200040, "popularity": 99, "explicit": False},
    {"id": "trk_002", "title": "Save Your Tears", "artist_id": "art_001", "album_id": "alb_001", "duration_ms": 215626, "popularity": 97, "explicit": False},
    {"id": "trk_003", "title": "Anti-Hero", "artist_id": "art_002", "album_id": "alb_002", "duration_ms": 200690, "popularity": 100, "explicit": False},
    {"id": "trk_004", "title": "Midnight Rain", "artist_id": "art_002", "album_id": "alb_002", "duration_ms": 174186, "popularity": 91, "explicit": False},
    {"id": "trk_005", "title": "Champagne Poetry", "artist_id": "art_003", "album_id": "alb_003", "duration_ms": 341946, "popularity": 89, "explicit": True},
    {"id": "trk_006", "title": "Happier Than Ever", "artist_id": "art_004", "album_id": "alb_004", "duration_ms": 298946, "popularity": 88, "explicit": False},
    {"id": "trk_007", "title": "Bad Habits", "artist_id": "art_005", "album_id": "alb_005", "duration_ms": 231041, "popularity": 94, "explicit": False},
    {"id": "trk_008", "title": "positions", "artist_id": "art_006", "album_id": "alb_006", "duration_ms": 172698, "popularity": 87, "explicit": False},
    {"id": "trk_009", "title": "Circles", "artist_id": "art_007", "album_id": "alb_007", "duration_ms": 215760, "popularity": 93, "explicit": False},
    {"id": "trk_010", "title": "Levitating", "artist_id": "art_008", "album_id": "alb_008", "duration_ms": 203807, "popularity": 96, "explicit": False},
    {"id": "trk_011", "title": "Physical", "artist_id": "art_008", "album_id": "alb_008", "duration_ms": 194000, "popularity": 85, "explicit": False},
    {"id": "trk_012", "title": "Starboy", "artist_id": "art_001", "album_id": "alb_001", "duration_ms": 230453, "popularity": 95, "explicit": True},
]

def enrich_track(track):
    artist = next((a for a in ARTISTS if a["id"] == track["artist_id"]), {})
    album = next((a for a in ALBUMS if a["id"] == track["album_id"]), {})
    return {**track, "artist_name": artist.get("name"), "album_title": album.get("title"), "album_cover": album.get("cover")}

@app.route("/health/live", methods=["GET"])
def liveness():
    return jsonify({"status": "alive", "service": "music-catalog", "version": SERVICE_VERSION}), 200

@app.route("/health/ready", methods=["GET"])
def readiness():
    uptime = time.time() - start_time
    if uptime < 3:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "tracks": len(TRACKS), "artists": len(ARTISTS), "albums": len(ALBUMS)}), 200

@app.route("/catalog/tracks", methods=["GET"])
def get_tracks():
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    tracks = [enrich_track(t) for t in TRACKS[offset:offset+limit]]
    return jsonify({"tracks": tracks, "total": len(TRACKS), "limit": limit, "offset": offset})

@app.route("/catalog/tracks/<track_id>", methods=["GET"])
def get_track(track_id):
    track = next((t for t in TRACKS if t["id"] == track_id), None)
    if not track:
        return jsonify({"error": "Track not found"}), 404
    return jsonify(enrich_track(track))

@app.route("/catalog/artists", methods=["GET"])
def get_artists():
    return jsonify({"artists": ARTISTS, "total": len(ARTISTS)})

@app.route("/catalog/artists/<artist_id>", methods=["GET"])
def get_artist(artist_id):
    artist = next((a for a in ARTISTS if a["id"] == artist_id), None)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404
    artist_tracks = [enrich_track(t) for t in TRACKS if t["artist_id"] == artist_id]
    return jsonify({**artist, "tracks": artist_tracks})

@app.route("/catalog/albums", methods=["GET"])
def get_albums():
    return jsonify({"albums": ALBUMS, "total": len(ALBUMS)})

@app.route("/catalog/albums/<album_id>", methods=["GET"])
def get_album(album_id):
    album = next((a for a in ALBUMS if a["id"] == album_id), None)
    if not album:
        return jsonify({"error": "Album not found"}), 404
    album_tracks = [enrich_track(t) for t in TRACKS if t["album_id"] == album_id]
    artist = next((a for a in ARTISTS if a["id"] == album["artist_id"]), {})
    return jsonify({**album, "artist": artist, "track_list": album_tracks})

@app.route("/catalog/trending", methods=["GET"])
def trending():
    sorted_tracks = sorted(TRACKS, key=lambda x: x["popularity"], reverse=True)
    return jsonify({"trending": [enrich_track(t) for t in sorted_tracks[:5]]})

@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "service": "music-catalog",
        "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time,
        "catalog_size": {"tracks": len(TRACKS), "artists": len(ARTISTS), "albums": len(ALBUMS)},
        "pod_name": os.environ.get("POD_NAME", "unknown"),
    })

if __name__ == "__main__":
    logger.info(f"Music Catalog Service v{SERVICE_VERSION} starting on port 5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
