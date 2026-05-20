# 🎵 Spotify-Inspired Self-Healing Kubernetes Infrastructure

## Architecture Overview

This project mimics Spotify's microservices architecture running on Minikube with full self-healing capabilities.

### Microservices
- **API Gateway** - Routes and load-balances all traffic
- **Auth Service** - JWT-based authentication
- **Music Catalog Service** - Song/album/artist data
- **Player Service** - Streaming state management
- **Recommendation Service** - Playlist generation
- **User Service** - User profiles & preferences
- **Search Service** - Full-text search
- **Frontend** - React-like Nginx-served SPA

### Self-Healing Features
- Liveness & Readiness Probes on every pod
- Horizontal Pod Autoscaler (HPA)
- Pod Disruption Budgets (PDB)
- Resource limits & requests
- Restart policies
- Rolling update strategies
- ConfigMaps & Secrets management

## Quick Start

```bash
# 1. Start Minikube
minikube start --cpus=4 --memory=8192

# 2. Build all Docker images
./scripts/build-all.sh

# 3. Deploy everything
./scripts/deploy-all.sh

# 4. Access the app
minikube service spotify-frontend --url
```
