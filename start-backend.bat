@echo off
echo Starting Threat Intelligence Summarizer Backend...
echo.
echo Backend will be available at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
