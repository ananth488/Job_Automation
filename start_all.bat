@echo off
title AI Job Automation - Launcher
echo Starting Backend (FastAPI on Port 8000)...
start "Backend Server" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --port 8000 --reload"

echo Starting Frontend (Next.js on Port 3000)...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Both servers are launching!
echo Frontend will be accessible at: http://localhost:3000
echo Backend API docs at: http://localhost:8000/docs
timeout /t 5

