"""
Search Service - Full-text search across catalog
Mimics Spotify's search infrastructure
"""

from flask import Flask, request, jsonify
import time, logging, os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()

SEARCH_INDEX = [
    {"id": "trk_001", "type": "track", "title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "icon": "🎵"},
    {"id": "trk_002", "type": "track", "title": "Save Your Tears", "artist": "The Weeknd", "album": "After Hours", "icon": "🎵"},
    {"id": "trk_003", "type": "track", "title": "Anti-Hero", "artist": "Taylor Swift", "album": "Midnights", "icon": "🎵"},
    {"id": "trk_004", "type": "track", "title": "Midnight Rain", "artist": "Taylor Swift", "album": "Midnights", "icon": "🎵"},
    {"id": "trk_005", "type": "track", "title": "Champagne Poetry", "artist": "Drake", "album": "Certified Lover Boy", "icon": "🎵"},
    {"id": "trk_006", "type": "track", "title": "Happier Than Ever", "artist": "Billie Eilish", "album": "Happier Than Ever", "icon": "🎵"},
    {"id": "trk_007", "type": "track", "title": "Bad Habits", "artist": "Ed Sheeran", "album": "Equals", "icon": "🎵"},
    {"id": "trk_010", "type": "track", "title": "Levitating", "artist": "Dua Lipa", "album": "Future Nostalgia", "icon": "🎵"},
    {"id": "art_001", "type": "artist", "title": "The Weeknd", "artist": "The Weeknd", "icon": "🎤"},
    {"id": "art_002", "type": "artist", "title": "Taylor Swift", "artist": "Taylor Swift", "icon": "🎸"},
    {"id": "art_003", "type": "artist", "title": "Drake", "artist": "Drake", "icon": "🎵"},
    {"id": "art_008", "type": "artist", "title": "Dua Lipa", "artist": "Dua Lipa", "icon": "🎙️"},
    {"id": "alb_001", "type": "album", "title": "After Hours", "artist": "The Weeknd", "icon": "🌙"},
    {"id": "alb_002", "type": "album", "title": "Midnights", "artist": "Taylor Swift", "icon": "⭐"},
    {"id": "alb_008", "type": "album", "title": "Future Nostalgia", "artist": "Dua Lipa", "icon": "🕺"},
]

SEARCH_HISTORY = []

@app.route("/health/live")
def liveness():
    return jsonify({"status": "alive", "service": "search", "version": SERVICE_VERSION}), 200

@app.route("/health/ready")
def readiness():
    uptime = time.time() - start_time
    if uptime < 2:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "index_size": len(SEARCH_INDEX)}), 200

@app.route("/search")
def search():
    query = request.args.get("q", "").lower().strip()
    type_filter = request.args.get("type", "all")
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    results = []
    for item in SEARCH_INDEX:
        if (type_filter == "all" or item["type"] == type_filter):
            score = 0
            if query in item["title"].lower():
                score += 10 if item["title"].lower().startswith(query) else 5
            if "artist" in item and query in item["artist"].lower():
                score += 3
            if score > 0:
                results.append({**item, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    SEARCH_HISTORY.append({"query": query, "results": len(results), "timestamp": time.time()})
    return jsonify({
        "query": query,
        "results": results[:limit],
        "total": len(results),
        "took_ms": round(time.time() * 1000 % 100, 2),
    })

@app.route("/search/trending")
def trending_searches():
    return jsonify({"trending": ["The Weeknd", "Taylor Swift", "Drake", "Billie Eilish", "Dua Lipa", "Ed Sheeran"]})

@app.route("/metrics")
def metrics():
    return jsonify({"service": "search-service", "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time, "index_size": len(SEARCH_INDEX),
        "total_searches": len(SEARCH_HISTORY), "pod_name": os.environ.get("POD_NAME", "unknown")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
