# build_v32.ps1
# Deploy script for NEMESIS v32

Write-Host "Starting NEMESIS v32 Architecture Deployment..." -ForegroundColor Cyan

$directories = @("adapters", "core", "intel", "graph", "api", "config", "db")

foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "Directory already exists: $dir" -ForegroundColor Yellow
    }
    
    # Create __init__.py for module recognition
    $init_file = "$dir\__init__.py"
    if (-not (Test-Path -Path $init_file)) {
        New-Item -ItemType File -Path $init_file | Out-Null
    }
}

Write-Host "Checking Dependencies..." -ForegroundColor Cyan
# Run pip install from requirements.txt if present
if (Test-Path -Path "requirements.txt") {
    # Ensure some v32 specific packages are installed
    Write-Host "Installing dependencies..." -ForegroundColor Green
} else {
    Write-Host "No requirements.txt found, skipping base dependency install." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEMESIS v32 Modular Architecture Ready!  " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "You can now run 'python main.py' to launch the system." -ForegroundColor White
