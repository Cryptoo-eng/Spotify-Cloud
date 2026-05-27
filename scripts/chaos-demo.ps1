# PowerShell script to demonstrate Kubernetes Self-Healing capabilities
Clear-Host
Write-Host '==========================================================' -ForegroundColor Magenta
Write-Host '[SPOTIFY CLOUD KUBERNETES SELF-HEALING DEMONSTRATION]' -ForegroundColor Magenta
Write-Host '==========================================================' -ForegroundColor Magenta
Write-Host ''

# Check if minikube is running
$clusterStatus = minikube status --format '{{.Host}}'
if ($clusterStatus -ne 'Running') {
    Write-Host 'Minikube is not running! Run minikube start first.' -ForegroundColor Red
    exit 1
}

Write-Host 'Active pods in spotify namespace:' -ForegroundColor Cyan
kubectl -n spotify get pods
Write-Host ''

# DEMO 1: POD DELETION & AUTO-RECOVERY
Write-Host 'Simulating Pod Crash (Sudden termination of container)...' -ForegroundColor Yellow
$targetPod = (kubectl -n spotify get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')

if (-not $targetPod) {
    Write-Host 'No pods found for auth-service. Make sure you deployed them first!' -ForegroundColor Red
    exit 1
}

Write-Host "Target: Killing active Pod: $targetPod" -ForegroundColor Red
kubectl -n spotify delete pod $targetPod --wait=$false

Write-Host 'Watching replica controller detect state drift and self-heal in real-time...' -ForegroundColor Yellow
Write-Host 'Press Ctrl+C to stop watching pods (showing for next 15 seconds)...' -ForegroundColor White

for ($i = 0; $i -lt 15; $i++) {
    Clear-Host
    Write-Host '==========================================================' -ForegroundColor Magenta
    Write-Host '[SPOTIFY CLOUD KUBERNETES SELF-HEALING DEMONSTRATION]' -ForegroundColor Magenta
    Write-Host '==========================================================' -ForegroundColor Magenta
    Write-Host ''
    Write-Host "Killed Pod: $targetPod" -ForegroundColor Red
    Write-Host "Recovery Progress (Tick $i/15):" -ForegroundColor Cyan
    kubectl -n spotify get pods -l app=auth-service
    Start-Sleep -Seconds 1
}

# DEMO 2: HORIZONTAL POD AUTOSCALER (HPA)
Write-Host ''
Write-Host 'Checking Auto-Scaling Configuration (HPA)...' -ForegroundColor Yellow
kubectl -n spotify get hpa

Write-Host ''
Write-Host 'To simulate high load and trigger HPA auto-scaling, execute this in a separate window:' -ForegroundColor Green
Write-Host 'kubectl -n spotify run load-generator --rm -i --tty --image=busybox:1.28 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://api-gateway:5000/api/catalog/trending; done"' -ForegroundColor Cyan

Write-Host ''
Write-Host 'Self-healing works seamlessly! The replica controller guarantees high availability.' -ForegroundColor Green
