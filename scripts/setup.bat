@echo off
REM EZSell Quick Setup Script for Windows
REM Double-click this file to set up the entire project

echo.
echo ============================================
echo    EZSell Setup Script for Windows
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
python --version

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found
node --version

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Please install npm.
    pause
    exit /b 1
)
echo [OK] npm found
npm --version
echo.

echo ============================================
echo    Setting up Backend...
echo ============================================
cd /d "%~dp0ezsell\ezsell\backend"

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Create database
echo Creating database...
python create_tables.py

REM Copy environment file
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

echo [OK] Backend setup complete!
echo.

echo ============================================
echo    Setting up Frontend...
echo ============================================
cd /d "%~dp0ezsell\ezsell\frontend"

REM Install dependencies
echo Installing Node.js dependencies (this may take a few minutes)...
call npm install

REM Copy environment file
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

echo [OK] Frontend setup complete!
echo.

echo ============================================
echo    Setup Complete!
echo ============================================
echo.
echo To start the application, use the start scripts:
echo.
echo 1. Backend: Double-click ezsell\ezsell\backend\start_backend.bat
echo    OR run: cd ezsell\ezsell\backend ^&^& start_backend.bat
echo.
echo 2. Frontend: Double-click ezsell\ezsell\frontend\start_frontend.bat
echo    OR run: cd ezsell\ezsell\frontend ^&^& start_frontend.bat
echo.
echo Then open: http://localhost:8080
echo.
pause
