"""
Recommendation Service - ML-based playlist generation
Mimics Spotify's Discover Weekly / algorithmic recommendations
"""

from flask import Flask, request, jsonify
import time, logging, os, random

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()

ALL_TRACKS = ["trk_001","trk_002","trk_003","trk_004","trk_005","trk_006","trk_007","trk_008","trk_009","trk_010","trk_011","trk_012"]

GENRE_TRACKS = {
    "pop": ["trk_001","trk_002","trk_003","trk_007","trk_010"],
    "r&b": ["trk_001","trk_002","trk_008"],
    "hip-hop": ["trk_005"],
    "alternative": ["trk_006"],
    "acoustic": ["trk_007"],
    "dance": ["trk_010","trk_011"],
}

PLAYLISTS = [
    {"id": "pl_001", "name": "Today's Top Hits", "description": "The biggest songs right now", "icon": "🔥", "tracks": ["trk_003","trk_001","trk_010","trk_007","trk_009","trk_002"]},
    {"id": "pl_002", "name": "Chill Vibes", "description": "Relax and unwind", "icon": "🌊", "tracks": ["trk_006","trk_004","trk_008","trk_011"]},
    {"id": "pl_003", "name": "Workout Mix", "description": "Power through your session", "icon": "💪", "tracks": ["trk_010","trk_012","trk_001","trk_003","trk_007"]},
    {"id": "pl_004", "name": "Late Night Drive", "description": "City lights and good music", "icon": "🌙", "tracks": ["trk_002","trk_006","trk_004","trk_011"]},
    {"id": "pl_005", "name": "Discover Weekly", "description": "Made for you", "icon": "🎯", "tracks": random.sample(ALL_TRACKS, 8)},
    {"id": "pl_006", "name": "Rap Caviar", "description": "Hip Hop's finest", "icon": "💎", "tracks": ["trk_005","trk_012","trk_003"]},
]

@app.route("/health/live")
def liveness():
    return jsonify({"status": "alive", "service": "recommendation", "version": SERVICE_VERSION}), 200

@app.route("/health/ready")
def readiness():
    uptime = time.time() - start_time
    if uptime < 3:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "playlists_loaded": len(PLAYLISTS)}), 200

@app.route("/recommendations/<user_id>")
def get_recommendations(user_id):
    """Simulated ML recommendations based on user ID"""
    seed = sum(ord(c) for c in user_id)
    random.seed(seed)
    tracks = random.sample(ALL_TRACKS, min(10, len(ALL_TRACKS)))
    random.seed()
    return jsonify({
        "user_id": user_id,
        "recommended_tracks": tracks,
        "algorithm": "collaborative_filtering_v2",
        "generated_at": time.time(),
    })

@app.route("/recommendations/playlists")
def get_playlists():
    return jsonify({"playlists": PLAYLISTS, "total": len(PLAYLISTS)})

@app.route("/recommendations/playlists/<playlist_id>")
def get_playlist(playlist_id):
    pl = next((p for p in PLAYLISTS if p["id"] == playlist_id), None)
    if not pl:
        return jsonify({"error": "Playlist not found"}), 404
    return jsonify(pl)

@app.route("/recommendations/similar/<track_id>")
def similar_tracks(track_id):
    """Find tracks similar to a given track"""
    others = [t for t in ALL_TRACKS if t != track_id]
    return jsonify({"track_id": track_id, "similar": random.sample(others, min(5, len(others)))})

@app.route("/metrics")
def metrics():
    return jsonify({"service": "recommendation-service", "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time, "playlists": len(PLAYLISTS),
        "pod_name": os.environ.get("POD_NAME", "unknown")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)
