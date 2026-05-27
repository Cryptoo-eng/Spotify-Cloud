# 🌐 expose-ngrok.ps1 - Automated Public Internet Tunneling Setup

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   ⚡ SPOTIFY-K8s NGROK TUNNEL ROUTER   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Ensure scripts run in the root workspace directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workDir = Split-Path -Parent $scriptDir
Set-Location $workDir

# 1. Verify kubectl is installed
$kubectlCheck = Get-Command kubectl -ErrorAction SilentlyContinue
if (!$kubectlCheck) {
    Write-Host "[ERROR] kubectl CLI is not installed or not in system PATH." -ForegroundColor Red
    Write-Host "Please install kubectl and verify your connection to Minikube first." -ForegroundColor Yellow
    Exit
}

# 2. Verify the frontend service is active in Kubernetes
Write-Host "[1/4] Verifying spotify-frontend status in 'spotify' namespace..." -ForegroundColor Cyan
$svc = kubectl get service spotify-frontend -n spotify -o jsonpath='{.metadata.name}' -ErrorAction SilentlyContinue
if (!$svc) {
    Write-Host "[ERROR] 'spotify-frontend' not found in 'spotify' namespace." -ForegroundColor Red
    Write-Host "Please ensure your cluster is running by running: ./scripts/deploy-all.ps1" -ForegroundColor Yellow
    Exit
}
Write-Host "✔️ 'spotify-frontend' found and active." -ForegroundColor Green

# 3. Check for local ngrok installation, or download it dynamically
Write-Host "[2/4] Checking for ngrok CLI..." -ForegroundColor Cyan
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
$ngrokLocalExe = Join-Path $workDir "ngrok.exe"

if ($ngrokPath) {
    $ngrokCmd = "ngrok"
    Write-Host "✔️ Global ngrok installation found at: $ngrokPath" -ForegroundColor Green
} elseif (Test-Path $ngrokLocalExe) {
    $ngrokCmd = ".\ngrok.exe"
    Write-Host "✔️ Local ngrok executable found in workspace directory." -ForegroundColor Green
} else {
    Write-Host "⚠️ ngrok not found. Downloading stable 64-bit ngrok executable dynamically..." -ForegroundColor Yellow
    $zipPath = Join-Path $workDir "ngrok.zip"
    $downloadUrl = "https://bin.equinox.io/c/bNy8QfgnMxD/ngrok-v3-stable-windows-amd64.zip"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath $workDir -Force
        Remove-Item $zipPath -Force
        $ngrokCmd = ".\ngrok.exe"
        Write-Host "✔️ ngrok downloaded and unpacked successfully!" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to download ngrok automatically. Please download it manually from https://ngrok.com" -ForegroundColor Red
        Exit
    }
}

# 4. Check/Prompt for Authtoken configuration
$ngrokConfigPath = Join-Path $env:USERPROFILE "AppData\Local\ngrok\ngrok.yml"
if (!(Test-Path $ngrokConfigPath)) {
    Write-Host ""
    Write-Host "⚠️  ATTENTION: ngrok requires an Authtoken to run tunnels." -ForegroundColor Yellow
    Write-Host "1. Sign up for a free account at: https://dashboard.ngrok.com" -ForegroundColor Cyan
    Write-Host "2. Copy your authtoken from the ngrok dashboard." -ForegroundColor Cyan
    Write-Host "3. Open a terminal and configure it by running:" -ForegroundColor Cyan
    Write-Host "   $ngrokCmd config add-authtoken <YOUR_TOKEN>" -ForegroundColor White
    Write-Host ""
}

# 5. Start Kubernetes Port-Forwarding in the background
Write-Host "[3/4] Launching Kubernetes Port-Forwarder in background (Port 8080 -> 80)..." -ForegroundColor Cyan
# Kill any existing kubectl port-forwards on 8080
Get-Process | Where-Object { $_.ProcessName -eq "kubectl" } | ForEach-Object {
    $cmd = $_.CommandLine
    if ($cmd -and $cmd.Contains("port-forward") -and $cmd.Contains("8080")) {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

$portForwardProcess = Start-Process -FilePath "kubectl" -ArgumentList "port-forward service/spotify-frontend 8080:80 -n spotify" -NoNewWindow -PassThru -ErrorAction SilentlyContinue

if (!$portForwardProcess) {
    Write-Host "[ERROR] Failed to start kubectl port-forward." -ForegroundColor Red
    Exit
}
Start-Sleep -Seconds 2
Write-Host "✔️ Port-forwarding established." -ForegroundColor Green

# 6. Start ngrok Tunnel
Write-Host "[4/4] Launching public ngrok HTTP tunnel on port 8080..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor White
Write-Host "   Press [Ctrl+C] inside the ngrok window to exit.      " -ForegroundColor Yellow
Write-Host "--------------------------------------------------------" -ForegroundColor White

Start-Sleep -Seconds 1
Start-Process -FilePath $ngrokCmd -ArgumentList "http 8080" -Wait
