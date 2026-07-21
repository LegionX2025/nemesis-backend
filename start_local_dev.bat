@echo off
color 0b
echo =======================================================
echo    NEMESIS - LIONSGATE NETWORK - LOCAL EDGE EMULATOR
echo =======================================================
echo.

echo [1/3] Booting Backend (FastAPI Edge Worker)...
start "Nemesis Backend" cmd /k "cd c:\Users\LEGIONX\Downloads\cases\local_deploy && call venv\Scripts\activate.bat && python backend\app\main.py"

echo [2/3] Booting Frontend (Cloudflare Pages Emulator)...
start "Nemesis Frontend" cmd /k "cd c:\Users\LEGIONX\Downloads\cases\cloudflare_frontend && python -m http.server 3001"

echo [3/3] Waiting for servers to initialize...
timeout /t 3 /nobreak > nul

echo Launching browser to http://localhost:3001/tracer.html
start http://localhost:3001/tracer.html

echo.
echo All systems are live. You can close this window.
echo Note: The servers are running in the two newly opened command prompt windows.
pause
