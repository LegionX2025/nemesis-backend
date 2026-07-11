@echo off
echo =======================================================
echo LIONSGATE INTELLIGENCE NETWORK - NEMESIS BOOTSTRAP
echo =======================================================
echo.
echo [1/3] Terminating any hanging processes on ports 8000, 3001, and 8088...
powershell -Command "Get-NetTCPConnection -LocalPort 8000, 3001, 8088 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force }"
echo Ports cleared.
echo.

echo [2/2] Booting Unified Engine (FastAPI + Frontend) on Port 8088...
start cmd /k "python backend\app\main.py"

echo.
echo =======================================================
echo BOOT SEQUENCE INITIATED.
echo Two new terminal windows should open for the frontend and backend.
echo Once both are fully running without errors, please reply back to the AI!
echo =======================================================
pause
