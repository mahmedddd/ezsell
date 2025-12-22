@echo off
REM EZSell Complete Setup Script for Windows
REM This script sets up both backend and frontend environments

echo ========================================
echo EZSell Project Setup
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js
echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version
echo.

REM Setup Backend
echo [3/6] Setting up Backend Virtual Environment...
cd backend
if exist venv (
    echo Virtual environment already exists, skipping creation...
) else (
    echo Creating virtual environment...
    python -m venv venv
)
echo.

echo [4/6] Installing Backend Dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Backend dependencies installed!
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env >nul 2>&1
    echo .env file created! Please update with your settings.
)

REM Initialize database
echo Initializing database...
python -c "from models.database import Base, engine; Base.metadata.create_all(engine); print('Database initialized!')"
echo.

deactivate
cd ..

REM Setup Frontend
echo [5/6] Setting up Frontend...
cd frontend
if exist node_modules (
    echo node_modules already exists, skipping installation...
) else (
    echo Installing frontend dependencies...
    call npm install
)
echo.

REM Create frontend .env if it doesn't exist
if not exist .env (
    echo Creating frontend .env file...
    copy .env.example .env >nul 2>&1
)

cd ..

echo [6/6] Setup Complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Update backend/.env with your configuration
echo 2. Update frontend/.env if needed
echo 3. Run start.bat to launch the application
echo.
echo To start the application manually:
echo   Backend:  cd backend ^&^& venv\Scripts\activate ^&^& python -m uvicorn main:app --reload
echo   Frontend: cd frontend ^&^& npm run dev
echo.
pause
