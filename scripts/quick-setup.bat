@echo off
REM Quick Setup Script for EZSell - One Command Setup for Windows
REM Double-click this file to set up everything

setlocal enabledelayedexpansion

echo.
echo =============================================
echo    EZSell - Quick Setup Script (Windows)
echo =============================================
echo.

REM Colors simulation (use echo with different markers)
set "OK=[OK]"
set "ERROR=[ERROR]"
set "INFO=[INFO]"
set "WARN=[WARNING]"

REM Check Python
echo Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Python not found. Please install Python 3.10+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo %OK% Python found
python --version

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Node.js not found. Please install Node.js 18+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo %OK% Node.js found
node --version

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% npm not found. Please install npm.
    pause
    exit /b 1
)
echo %OK% npm found
npm --version

echo.
echo =============================================
echo    Setting up Backend...
echo =============================================
echo.

REM Navigate to backend
cd /d "%~dp0ezsell\ezsell\backend"

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo %OK% Virtual environment created
) else (
    echo %INFO% Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install dependencies
echo Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    echo %OK% Dependencies installed
) else (
    echo %WARN% requirements.txt not found, installing core packages...
    pip install fastapi uvicorn sqlalchemy pydantic python-multipart --quiet
    pip install pandas numpy scikit-learn joblib --quiet
    pip install python-jose passlib bcrypt python-dotenv --quiet
    pip install requests beautifulsoup4 --quiet
    echo %OK% Core packages installed
)

REM Create database
echo Setting up database...
if exist "create_tables.py" (
    python create_tables.py
) else (
    python -c "from models.database import Base, engine; Base.metadata.create_all(engine); print('Database created')"
)
echo %OK% Database setup complete

REM Create required directories
echo Creating required directories...
if not exist "uploads\listings" mkdir "uploads\listings"
if not exist "data\ar_previews" mkdir "data\ar_previews"
if not exist "scraped_data\mobile" mkdir "scraped_data\mobile"
if not exist "scraped_data\laptop" mkdir "scraped_data\laptop"
if not exist "scraped_data\furniture" mkdir "scraped_data\furniture"
if not exist "models_enhanced" mkdir "models_enhanced"
if not exist "trained_models" mkdir "trained_models"
echo %OK% Directories created

echo.
echo =============================================
echo    Setting up Frontend...
echo =============================================
echo.

REM Navigate to frontend
cd /d "%~dp0ezsell\ezsell\frontend"

REM Install frontend dependencies
echo Installing frontend dependencies...
if exist "package.json" (
    call npm install
    echo %OK% Frontend dependencies installed
) else (
    echo %ERROR% package.json not found in frontend directory
    pause
    exit /b 1
)

echo.
echo =============================================
echo    Setup Complete!
echo =============================================
echo.
echo To start the application:
echo.
echo 1. Backend (in one terminal):
echo    cd ezsell\ezsell\backend
echo    venv\Scripts\activate
echo    python -m uvicorn main:app --reload --port 8000
echo.
echo 2. Frontend (in another terminal):
echo    cd ezsell\ezsell\frontend
echo    npm run dev
echo.
echo 3. Open browser to: http://localhost:8080
echo.
echo Or use the provided batch files:
echo    - Backend: ezsell\ezsell\backend\start.bat
echo    - Frontend: ezsell\ezsell\frontend\start.bat
echo.
echo Happy coding! 🚀
echo.
pause
