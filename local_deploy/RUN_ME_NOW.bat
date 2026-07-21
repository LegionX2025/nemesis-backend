@echo off
echo ====================================================
echo NEMESIS v3 - ONE-CLICK DEPLOYMENT ^& FIX ENGINE
echo ====================================================
echo.
echo [1/4] Cleaning up Vercel/Render and Fixing Frontend Theme...
python scripts\fix_all_and_cleanup.py
echo.
echo [2/4] Injecting GitHub Automation and Missing Endpoints...
python scripts\inject_github.py
python scripts\add_full_endpoints.py
echo.
echo [3/4] Deploying Backend to Cloudflare ^& Pushing to GitHub...
python deployer.py
echo.
echo [4/4] Deploying Frontend to Cloudflare Pages...
call deploy_frontend.bat
echo.
echo ====================================================
echo DEPLOYMENT COMPLETE!
echo ====================================================
pause
