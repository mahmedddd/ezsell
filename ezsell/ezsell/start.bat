@echo off
REM EZSell Application Launcher for Windows

echo ========================================
echo Starting EZSell Application
echo ========================================
echo.

REM Start Backend
echo Starting Backend Server...
start "EZSell Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

REM Start Frontend
echo Starting Frontend Server...
start "EZSell Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3 >nul

echo.
echo ========================================
echo Application Started!
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8080
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause >nul

REM Stop servers
echo Stopping servers...
taskkill /FI "WindowTitle eq EZSell Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq EZSell Frontend*" /F >nul 2>&1
echo Servers stopped.
