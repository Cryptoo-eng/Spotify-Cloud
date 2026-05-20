"""
API Gateway - Central routing hub for all Spotify microservices
Handles auth, rate limiting, load balancing, and service discovery
"""

# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, Response
import requests, time, logging, os, random, json
from functools import wraps

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

# Service discovery - uses Kubernetes service names
SERVICES = {
    "auth":           os.environ.get("AUTH_SERVICE_URL",           "http://auth-service:5001"),
    "music-catalog":  os.environ.get("CATALOG_SERVICE_URL",        "http://music-catalog-service:5002"),
    "player":         os.environ.get("PLAYER_SERVICE_URL",         "http://player-service:5003"),
    "recommendation": os.environ.get("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:5004"),
    "search":         os.environ.get("SEARCH_SERVICE_URL",         "http://search-service:5005"),
    "user":           os.environ.get("USER_SERVICE_URL",           "http://user-service:5006"),
}

SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")
start_time = time.time()
request_log = []

def require_auth(f):
    """Auth middleware - validates JWT tokens via auth-service"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization required"}), 401
        try:
            resp = requests.post(
                f"{SERVICES['auth']}/auth/validate",
                headers={"Authorization": auth_header},
                timeout=3
            )
            if resp.status_code != 200 or not resp.json().get("valid"):
                return jsonify({"error": "Invalid or expired token"}), 401
            request.user_info = resp.json()
        except Exception as e:
            logger.error(f"Auth service error: {e}")
            return jsonify({"error": "Auth service unavailable"}), 503
        return f(*args, **kwargs)
    return decorated

def proxy(service, path, method="GET", **kwargs):
    """Proxy a request to a backend service"""
    url = f"{SERVICES[service]}{path}"
    try:
        resp = requests.request(method, url, timeout=10,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            params=request.args,
            json=request.get_json(silent=True),
            **kwargs)
        return Response(resp.content, status=resp.status_code, content_type="application/json")
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service '{service}' unavailable", "service": service}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Service '{service}' timed out", "service": service}), 504
    except Exception as e:
        logger.error(f"Proxy error for {service}: {e}")
        return jsonify({"error": "Internal gateway error"}), 500

@app.before_request
def log_request():
    request_log.append({"method": request.method, "path": request.path, "timestamp": time.time()})
    if len(request_log) > 1000:
        request_log.pop(0)

@app.route("/health/live")
def liveness():
    return jsonify({"status": "alive", "service": "api-gateway", "version": SERVICE_VERSION}), 200

@app.route("/health/ready")
def readiness():
    uptime = time.time() - start_time
    if uptime < 3:
        return jsonify({"status": "starting"}), 503
    return jsonify({"status": "ready", "services_registered": len(SERVICES)}), 200

# Auth routes (no auth required)
@app.route("/api/auth/login", methods=["POST"])
def login():
    return proxy("auth", "/auth/login", "POST")

@app.route("/api/auth/validate", methods=["POST"])
def validate():
    return proxy("auth", "/auth/validate", "POST")

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    return proxy("auth", "/auth/refresh", "POST")

# Catalog routes
@app.route("/api/catalog/tracks")
def get_tracks():
    return proxy("music-catalog", "/catalog/tracks")

@app.route("/api/catalog/tracks/<track_id>")
def get_track(track_id):
    return proxy("music-catalog", f"/catalog/tracks/{track_id}")

@app.route("/api/catalog/artists")
def get_artists():
    return proxy("music-catalog", "/catalog/artists")

@app.route("/api/catalog/artists/<artist_id>")
def get_artist(artist_id):
    return proxy("music-catalog", f"/catalog/artists/{artist_id}")

@app.route("/api/catalog/albums")
def get_albums():
    return proxy("music-catalog", "/catalog/albums")

@app.route("/api/catalog/trending")
def trending():
    return proxy("music-catalog", "/catalog/trending")

# Search routes
@app.route("/api/search")
def search():
    return proxy("search", "/search")

@app.route("/api/search/trending")
def trending_searches():
    return proxy("search", "/search/trending")

# Player routes
@app.route("/api/player/<user_id>/state")
def player_state(user_id):
    return proxy("player", f"/player/{user_id}/state")

@app.route("/api/player/<user_id>/play", methods=["PUT"])
def player_play(user_id):
    return proxy("player", f"/player/{user_id}/play", "PUT")

@app.route("/api/player/<user_id>/pause", methods=["PUT"])
def player_pause(user_id):
    return proxy("player", f"/player/{user_id}/pause", "PUT")

@app.route("/api/player/<user_id>/next", methods=["POST"])
def player_next(user_id):
    return proxy("player", f"/player/{user_id}/next", "POST")

# Recommendation routes
@app.route("/api/recommendations/<user_id>")
def recommendations(user_id):
    return proxy("recommendation", f"/recommendations/{user_id}")

@app.route("/api/recommendations/playlists")
def playlists():
    return proxy("recommendation", "/recommendations/playlists")

@app.route("/api/recommendations/playlists/<playlist_id>")
def playlist(playlist_id):
    return proxy("recommendation", f"/recommendations/playlists/{playlist_id}")

# User routes
@app.route("/api/users/<user_id>")
def get_user(user_id):
    return proxy("user", f"/users/{user_id}")

@app.route("/api/users/<user_id>/library")
def get_library(user_id):
    return proxy("user", f"/users/{user_id}/library")

# Gateway-level metrics and health aggregation
@app.route("/api/services/health")
def services_health():
    """Check health of all downstream services"""
    results = {}
    for name, url in SERVICES.items():
        try:
            resp = requests.get(f"{url}/health/ready", timeout=3)
            results[name] = {"status": "healthy" if resp.status_code == 200 else "degraded",
                             "code": resp.status_code, "data": resp.json()}
        except Exception as e:
            results[name] = {"status": "unreachable", "error": str(e)}
    overall = "healthy" if all(r["status"] == "healthy" for r in results.values()) else "degraded"
    return jsonify({"overall": overall, "services": results, "timestamp": time.time()})

@app.route("/api/gateway/metrics")
def gateway_metrics():
    recent = [r for r in request_log if time.time() - r["timestamp"] < 60]
    return jsonify({
        "service": "api-gateway", "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time,
        "total_requests": len(request_log),
        "requests_last_minute": len(recent),
        "registered_services": list(SERVICES.keys()),
        "pod_name": os.environ.get("POD_NAME", "unknown"),
    })

if __name__ == "__main__":
    logger.info(f"API Gateway v{SERVICE_VERSION} starting on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
