@echo off
echo =======================================================
echo LIONSGATE INTELLIGENCE NETWORK - NEMESIS BOOTSTRAP
echo =======================================================
echo.
echo [1/3] Terminating any hanging processes on ports 8000 and 8088...
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr :8000') DO (
    IF NOT "%%T"=="0" taskkill /PID %%T /F 2>NUL
)
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr :8088') DO (
    IF NOT "%%T"=="0" taskkill /PID %%T /F 2>NUL
)
echo Ports cleared.
echo.

echo [2/3] Booting Backend Engine (FastAPI) on Port 8088...
start cmd /k "cd backend\app && python -m uvicorn main:app --host 127.0.0.1 --port 8088"

echo [3/3] Booting Frontend UI on Port 8000...
start cmd /k "cd frontend\templates && python -m http.server 8000"

echo.
echo =======================================================
echo BOOT SEQUENCE INITIATED.
echo Two new terminal windows should open for the frontend and backend.
echo Once both are fully running without errors, please reply back to the AI!
echo =======================================================
pause
