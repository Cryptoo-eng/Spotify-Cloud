"""
Auth Service - JWT-based authentication mimicking Spotify's auth flow
Handles login, token refresh, and token validation
"""

from flask import Flask, request, jsonify
import jwt
import datetime
import hashlib
import random
import time
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

SECRET_KEY = os.environ.get("JWT_SECRET", "spotify-k8s-super-secret-2024")
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")

# Simulated user DB
USERS = {
    "john@spotify.com": {"password": hashlib.sha256("password123".encode()).hexdigest(), "plan": "premium", "id": "usr_001"},
    "jane@spotify.com": {"password": hashlib.sha256("music4ever".encode()).hexdigest(), "plan": "free", "id": "usr_002"},
    "admin@spotify.com": {"password": hashlib.sha256("adminpass".encode()).hexdigest(), "plan": "premium", "id": "usr_003"},
}

start_time = time.time()
request_count = 0

@app.route("/health/live", methods=["GET"])
def liveness():
    """Kubernetes liveness probe - is the process alive?"""
    return jsonify({"status": "alive", "service": "auth", "version": SERVICE_VERSION}), 200

@app.route("/health/ready", methods=["GET"])
def readiness():
    """Kubernetes readiness probe - is the service ready to handle traffic?"""
    uptime = time.time() - start_time
    if uptime < 5:
        return jsonify({"status": "starting", "uptime": uptime}), 503
    return jsonify({"status": "ready", "uptime": uptime, "users_loaded": len(USERS)}), 200

@app.route("/auth/login", methods=["POST"])
def login():
    global request_count
    request_count += 1
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = USERS.get(email)
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if not user or user["password"] != hashed:
        return jsonify({"error": "Invalid credentials"}), 401

    payload = {
        "sub": user["id"],
        "email": email,
        "plan": user["plan"],
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    logger.info(f"User {email} logged in successfully")
    return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": 3600})

@app.route("/auth/validate", methods=["POST"])
def validate():
    global request_count
    request_count += 1
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        data = request.get_json() or {}
        token = data.get("token", "")

    if not token:
        return jsonify({"valid": False, "error": "No token provided"}), 401

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "user_id": payload["sub"], "plan": payload["plan"], "email": payload["email"]})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"valid": False, "error": str(e)}), 401

@app.route("/auth/refresh", methods=["POST"])
def refresh():
    """Simulate token refresh"""
    data = request.get_json() or {}
    old_token = data.get("token", "")
    try:
        payload = jwt.decode(old_token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        payload["iat"] = datetime.datetime.utcnow()
        payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        new_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"access_token": new_token, "token_type": "Bearer", "expires_in": 3600})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "service": "auth-service",
        "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - start_time,
        "total_requests": request_count,
        "users_count": len(USERS),
        "pod_name": os.environ.get("POD_NAME", "unknown"),
        "node_name": os.environ.get("NODE_NAME", "unknown"),
    })

if __name__ == "__main__":
    logger.info(f"Auth Service v{SERVICE_VERSION} starting on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
