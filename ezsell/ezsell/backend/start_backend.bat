@echo off
cd /d "c:\Users\ahmed\Downloads\ezsell\ezsell\ezsell\backend"
echo Starting EZSell Backend Server...
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
