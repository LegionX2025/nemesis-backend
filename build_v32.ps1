# NEMESIS v32 Production Build Script

Write-Host "[*] Booting NEMESIS v32 Build Pipeline..." -ForegroundColor Cyan

# Install baseline graph and neural dependencies
Write-Host "[*] Installing Graph Neural Inference Dependencies..."
pip install networkx torch pydantic "fastapi[all]" web3 aiohttp

# Create architecture directories if they don't exist
$dirs = @("adapters", "intel", "graph", "core", "api", "scratch")
foreach ($dir in $dirs) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "[+] Created directory $dir" -ForegroundColor Green
    }
}

Write-Host "[+] NEMESIS v32 Architecture fully instantiated." -ForegroundColor Green
Write-Host "[*] To run the system, execute: python nemesis_v32.py"
