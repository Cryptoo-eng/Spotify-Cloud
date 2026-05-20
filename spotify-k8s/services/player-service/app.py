"""
Player Service - Streaming state management
Manages playback sessions, queue, and real-time state
"""

from flask import Flask, request, jsonify
import time, logging, os, random, threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()
SESSIONS = {}
PLAY_HISTORY = []
lock = threading.Lock()

TRACK_IDS = ["trk_001","trk_002","trk_003","trk_004","trk_005","trk_006","trk_007","trk_008","trk_009","trk_010","trk_011","trk_012"]

def get_session(user_id):
    with lock:
        if user_id not in SESSIONS:
            SESSIONS[user_id] = {"user_id": user_id, "current_track": None, "queue": [],
                "is_playing": False, "volume": 80, "shuffle": False, "repeat": "off",
                "position_ms": 0, "device": "Web Player", "started_at": None}
        return SESSIONS[user_id]

@app.route("/health/live")
def liveness():
    return jsonify({"status": "alive", "service": "player", "version": SERVICE_VERSION}), 200

@app.route("/health/ready")
def readiness():
    uptime = time.time() - start_time
    if uptime < 3:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "active_sessions": len(SESSIONS)}), 200

@app.route("/player/<user_id>/state")
def get_state(user_id):
    session = get_session(user_id)
    if session["is_playing"] and session["started_at"]:
        session["position_ms"] = min(int((time.time() - session["started_at"]) * 1000), 240000)
    return jsonify(session)

@app.route("/player/<user_id>/play", methods=["PUT"])
def play(user_id):
    data = request.get_json() or {}
    session = get_session(user_id)
    with lock:
        if data.get("track_id"):
            session["current_track"] = data["track_id"]
        session["is_playing"] = True
        session["started_at"] = time.time()
        session["position_ms"] = data.get("position_ms", 0)
    PLAY_HISTORY.append({"user_id": user_id, "track_id": session["current_track"], "timestamp": time.time()})
    return jsonify({"status": "playing", "track": session["current_track"]})

@app.route("/player/<user_id>/pause", methods=["PUT"])
def pause(user_id):
    session = get_session(user_id)
    with lock:
        session["is_playing"] = False
        if session["started_at"]:
            session["position_ms"] = min(int((time.time() - session["started_at"]) * 1000), 240000)
    return jsonify({"status": "paused", "position_ms": session["position_ms"]})

@app.route("/player/<user_id>/next", methods=["POST"])
def next_track(user_id):
    session = get_session(user_id)
    with lock:
        session["current_track"] = session["queue"].pop(0) if session["queue"] else random.choice(TRACK_IDS)
        session["position_ms"] = 0
        session["started_at"] = time.time()
        session["is_playing"] = True
    return jsonify({"status": "playing", "track": session["current_track"]})

@app.route("/player/<user_id>/volume", methods=["PUT"])
def set_volume(user_id):
    data = request.get_json() or {}
    volume = max(0, min(100, int(data.get("volume", 80))))
    get_session(user_id)["volume"] = volume
    return jsonify({"volume": volume})

@app.route("/metrics")
def metrics():
    active = sum(1 for s in SESSIONS.values() if s["is_playing"])
    return jsonify({"service": "player-service", "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time, "total_sessions": len(SESSIONS),
        "active_streams": active, "total_plays": len(PLAY_HISTORY),
        "pod_name": os.environ.get("POD_NAME", "unknown")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
