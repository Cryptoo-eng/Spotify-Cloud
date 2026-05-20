"""
User Service - User profiles, preferences, and library management
"""

from flask import Flask, request, jsonify
import time, logging, os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()

USERS = {
    "usr_001": {
        "id": "usr_001", "name": "John Doe", "email": "john@spotify.com",
        "plan": "premium", "country": "US", "avatar": "👨",
        "following_artists": ["art_001", "art_002", "art_008"],
        "saved_tracks": ["trk_001", "trk_003", "trk_010"],
        "created_playlists": ["pl_001", "pl_004"],
        "joined": "2021-03-15", "followers": 42,
    },
    "usr_002": {
        "id": "usr_002", "name": "Jane Smith", "email": "jane@spotify.com",
        "plan": "free", "country": "UK", "avatar": "👩",
        "following_artists": ["art_002", "art_004"],
        "saved_tracks": ["trk_003", "trk_006", "trk_011"],
        "created_playlists": ["pl_002"],
        "joined": "2022-07-20", "followers": 15,
    },
}

@app.route("/health/live")
def liveness():
    return jsonify({"status": "alive", "service": "user", "version": SERVICE_VERSION}), 200

@app.route("/health/ready")
def readiness():
    uptime = time.time() - start_time
    if uptime < 2:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "users_loaded": len(USERS)}), 200

@app.route("/users/<user_id>")
def get_user(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)

@app.route("/users/<user_id>/library")
def get_library(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"saved_tracks": user["saved_tracks"], "playlists": user["created_playlists"],
        "following": user["following_artists"]})

@app.route("/users/<user_id>/save", methods=["POST"])
def save_track(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json() or {}
    track_id = data.get("track_id")
    if track_id and track_id not in user["saved_tracks"]:
        user["saved_tracks"].append(track_id)
    return jsonify({"saved": True, "library_size": len(user["saved_tracks"])})

@app.route("/users/<user_id>/follow", methods=["POST"])
def follow_artist(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json() or {}
    artist_id = data.get("artist_id")
    if artist_id and artist_id not in user["following_artists"]:
        user["following_artists"].append(artist_id)
    return jsonify({"following": True, "total_following": len(user["following_artists"])})

@app.route("/metrics")
def metrics():
    return jsonify({"service": "user-service", "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time, "total_users": len(USERS),
        "pod_name": os.environ.get("POD_NAME", "unknown")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=False)
