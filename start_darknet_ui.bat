@echo off
title LIONSGATE NEMESIS OSINT ^& DARKNET CRAWLER
cd /d "%~dp0"
call venv\Scripts\activate
python darknet\darknetv2.py
pause
