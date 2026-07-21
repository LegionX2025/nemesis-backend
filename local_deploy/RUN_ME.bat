@echo off
echo ==========================================
echo NEMESIS EDGE DEPLOYMENT SCRIPT
echo ==========================================
echo Fixing Frontend URLs...
python deploy_edge_api.py
echo.
echo If the deployment succeeded, close this window.
pause
