# PowerShell script to build all Docker container images inside Minikube's Docker daemon
Write-Host "🎵 [SPOTIFY CLOUD] Pointing PowerShell session to Minikube Docker Daemon..." -ForegroundColor Cyan

# Point docker CLI to minikube's internal docker host
& minikube docker-env | Invoke-Expression

$services = @(
    "api-gateway",
    "auth-service",
    "music-catalog",
    "player-service",
    "recommendation-service",
    "search-service",
    "user-service",
    "frontend"
)

foreach ($service in $services) {
    $service = $service.Trim()
    Write-Host "🐳 Building Docker image for: $service..." -ForegroundColor Yellow
    $dir = Join-Path "services" $service
    if ($service -eq "music-catalog") {
        $tag = "spotify/music-catalog-service:latest"
    } elseif ($service -eq "frontend") {
        $tag = "spotify/spotify-frontend:latest"
    } else {
        $tag = "spotify/${service}:latest"
    }
    
    docker build -t $tag $dir
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully built $tag" -ForegroundColor Green
    } else {
        Write-Error "❌ Failed to build $tag"
        exit 1
    }
}

Write-Host "🎉 All images successfully built inside Minikube!" -ForegroundColor Green
