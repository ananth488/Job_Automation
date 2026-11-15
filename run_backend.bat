@echo off
title AI Job Automation - Backend Server (Port 8000)
cd /d "%~dp0backend"
echo ===================================================
echo Starting FastAPI Backend Server on port 8000...
echo Keep this window open while using the application.
echo ===================================================
python -m uvicorn main:app --port 8000 --reload
pause

