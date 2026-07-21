@echo off
echo Running Refactor Script...
python refactor.py
echo.
echo Installing Dependencies...
pip install -r productions\requirements.txt
echo.
echo Starting Productions Server...
echo The server will now run in this window. Open http://localhost:8000 in your browser.
python productions\app.py
