# PowerShell script to deploy Spotify Self-Healing platform to Minikube K8s cluster
Write-Host "🎵 [SPOTIFY CLOUD] Deploying to Kubernetes namespace 'spotify'..." -ForegroundColor Cyan

# Create namespace first
Write-Host "📦 Creating Namespace..." -ForegroundColor Yellow
kubectl apply -f k8s/00-namespace.yaml

# Apply ConfigMaps & Secrets
Write-Host "🔐 Configuring ConfigMaps and Secrets..." -ForegroundColor Yellow
kubectl apply -f k8s/01-configmap-secrets.yaml

# Apply auth service
Write-Host "🔑 Deploying Auth Service..." -ForegroundColor Yellow
kubectl apply -f k8s/02-auth-service.yaml

# Apply catalog and player
Write-Host "💿 Deploying Catalog & Player Services..." -ForegroundColor Yellow
kubectl apply -f k8s/03-catalog-player.yaml

# Apply other backends
Write-Host "🧠 Deploying Search, User & Recommendation Services..." -ForegroundColor Yellow
kubectl apply -f k8s/04-recommendation-search-user.yaml

# Apply API Gateway
Write-Host "🛡️ Deploying API Gateway..." -ForegroundColor Yellow
kubectl apply -f k8s/05-api-gateway.yaml

# Apply Frontend
Write-Host "📺 Deploying Nginx Web Frontend..." -ForegroundColor Yellow
kubectl apply -f k8s/06-frontend.yaml

Write-Host "⏳ Waiting for pods to initialize (readiness checks in progress)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
kubectl -n spotify get pods -o wide

Write-Host "🎉 Platform deployed! To get the web frontend URL run:" -ForegroundColor Green
Write-Host "minikube service -n spotify spotify-frontend" -ForegroundColor Cyan
