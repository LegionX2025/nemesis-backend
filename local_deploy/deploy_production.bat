@echo off
echo ========================================================
echo NEMESIS PRODUCTION DEPLOYMENT
echo ========================================================
echo.
echo [1] Pre-processing Frontend HTML Files...
cd /d "C:\Users\LEGIONX\Downloads\cases\local_deploy"
python fix_frontend.py
if %ERRORLEVEL% neq 0 (
    echo Failed to fix frontend. Aborting.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2] Deploying Backend Worker (nemesis-api-v3)...
cd /d "C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis-global-worker"
call npx wrangler deploy
if %ERRORLEVEL% neq 0 (
    echo Failed to deploy backend. Aborting.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3] Deploying Frontend to Cloudflare Pages...
cd /d "C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"
call npx wrangler pages deploy . --project-name=nemesis-id-frontend --commit-dirty=true
if %ERRORLEVEL% neq 0 (
    echo Failed to deploy frontend. Aborting.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo Deployment process finished successfully!
echo ========================================================
pause
