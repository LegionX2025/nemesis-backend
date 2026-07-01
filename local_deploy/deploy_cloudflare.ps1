# Ensure Wrangler is installed
Write-Host "Installing/Updating Cloudflare Wrangler..." -ForegroundColor Cyan
npm install -g wrangler

# Create the Cloudflare Queue
Write-Host "`nCreating Cloudflare Queue: nemesis-trace-queue..." -ForegroundColor Cyan
# This might fail if the queue already exists, which is fine, we continue
wrangler queues create nemesis-trace-queue

# Deploy the Consumer Worker
Write-Host "`nDeploying the Queue Consumer Worker..." -ForegroundColor Cyan
Set-Location -Path "C:\Users\LEGIONX\Downloads\cases\local_deploy\worker_consumer"
wrangler deploy
if ($LASTEXITCODE -ne 0) {
    Write-Host "Worker deployment failed. Ensure you have the Workers Paid plan for Queues." -ForegroundColor Red
}

# Deploy the Pages Frontend & API Gateway
Write-Host "`nDeploying the Frontend & Pages Functions..." -ForegroundColor Cyan
Set-Location -Path "C:\Users\LEGIONX\Downloads\cases\local_deploy\templates"
# We deploy the current directory (templates). The functions/ folder is automatically detected.
wrangler pages deploy . --project-name nemesis-id-frontend

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "IMPORTANT: You must set the PYTHON_BACKEND_URL environment variable in both the Worker and the Pages project via the Cloudflare Dashboard to point to your cloudflared tunnel URL." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
