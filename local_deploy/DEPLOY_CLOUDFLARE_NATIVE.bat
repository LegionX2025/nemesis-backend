@echo off
echo ========================================================
echo CLOUDFLARE NATIVE EDGE DEPLOYMENT
echo ========================================================
echo.
echo [1] Skipping file overrides (UI files are already updated locally).

echo.
echo [2] Deploying TypeScript Edge API (nemesis-api)...
cd /d "C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis-global-worker"
call npx wrangler deploy

echo.
echo [2] Deploying Frontend to Cloudflare Pages...
cd /d "C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"
call npx wrangler pages deploy . --project-name=nemesis-id-frontend --commit-dirty=true

echo.
echo ========================================================
echo Deployment process finished. Please review the output above.
echo ========================================================
pause
