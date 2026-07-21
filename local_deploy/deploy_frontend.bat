@echo off
echo ====================================================
echo NEMESIS v3 Frontend Cloudflare Pages Deployment
echo ====================================================
echo.
echo Deploying ./frontend to Cloudflare Pages...
call npx wrangler pages deploy ./frontend --project-name nemesis-frontend
echo.
echo Deployment Complete!
pause
