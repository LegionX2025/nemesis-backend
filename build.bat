@echo off
echo ========================================================
echo NEMESIS v32 OmniChain Intelligence OS 
echo Autonomous Multi-Chain Intelligence OS Deployment Script
echo ========================================================

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH! Please install Python 3.9+
    pause
    exit /b
)

echo [2/3] Installing / Verifying Dependencies...
pip install -r requirements.txt
pip install eventlet==0.40.3 motor pymongo uvicorn fastapi websockets aiohttp python-dotenv

echo [3/3] Launching NEMESIS v32 Core Engine...
echo Server starting on http://localhost:8000
python main.py

pause
