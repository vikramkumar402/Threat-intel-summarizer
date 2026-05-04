@echo off
title Threat Intelligence Summarizer
color 0A

echo ============================================================
echo    THREAT INTELLIGENCE SUMMARIZER - STARTUP
echo ============================================================
echo.

cd backend

echo [1/3] Starting Backend Server...
start "Backend API" cmd /k "python run.py"
timeout /t 3 /nobreak >nul

echo [2/3] Opening API Documentation...
start http://localhost:8000/docs

echo [3/3] Opening Frontend Application...
cd ..\frontend
start index-simple.html

echo.
echo ============================================================
echo    APPLICATION STARTED SUCCESSFULLY!
echo ============================================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend:     Opened in your browser
echo.
echo Press any key to close this window...
pause >nul
