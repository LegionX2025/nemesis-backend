@echo off
echo ========================================================
echo DEPLOYING PATCHED NEMESIS BACKEND AND FRONTEND
echo ========================================================
echo.
echo [1] Deploying Python Backend to Cloudflare Workers...
cd c:\Users\LEGIONX\Downloads\cases\local_deploy\backend
call npx wrangler deploy

echo.
echo [2] Deploying Frontend to Cloudflare Pages...
cd c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend
call npx wrangler pages deploy . --project-name nemesis-id-frontend

echo.
echo ========================================================
echo DEPLOYMENT COMPLETE! Please return to the AI chat.
echo ========================================================
pause
