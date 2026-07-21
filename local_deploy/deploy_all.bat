@echo off
echo ========================================================
echo NEMESIS EDGE DEPLOYMENT PIPELINE
echo ========================================================
echo.
echo [1] Copying tracer_scripts from Nemesis to local_deploy...
xcopy /E /I /Y "C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts" "c:\Users\LEGIONX\Downloads\cases\local_deploy\tracer_scripts"

echo.
echo [2] Running Auto Deployer...
cd /d "c:\Users\LEGIONX\Downloads\cases\local_deploy"
python auto_deploy.py

echo.
echo ========================================================
echo Deployment process finished. Please review the output above.
echo ========================================================
pause
