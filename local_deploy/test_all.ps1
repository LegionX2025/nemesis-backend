# NEMESIS Production Test Suite Runner

Write-Host "=================================================="
Write-Host "   INITIATING NEMESIS PLATFORM TEST SUITE         "
Write-Host "=================================================="

# Check if Python is available
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# Ensure virtual environment is active or use global python
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNING: Virtual environment not detected. Running with global Python." -ForegroundColor Yellow
}

Write-Host ">>> [1/3] Installing/Verifying Test Dependencies..."
python -m pip install -q -r backend/requirements.txt pytest httpx

Write-Host ">>> [2/3] Running Backend Tests (pytest)..."
python -m pytest backend/tests/ -v

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend tests failed. Halting deployment."
    exit $LASTEXITCODE
}


Write-Host "=================================================="
Write-Host "   ALL TESTS PASSED - SYSTEM READY FOR DEPLOY     "
Write-Host "=================================================="
exit 0
