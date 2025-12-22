#!/bin/bash
# EZSell Complete Setup Script for Linux/Mac
# This script sets up both backend and frontend environments

echo "========================================"
echo "EZSell Project Setup"
echo "========================================"
echo

# Check Python
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi
python3 --version
echo

# Check Node.js
echo "[2/6] Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
node --version
npm --version
echo

# Setup Backend
echo "[3/6] Setting up Backend Virtual Environment..."
cd backend
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation..."
else
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
echo

echo "[4/6] Installing Backend Dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Backend dependencies installed!"
echo

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env 2>/dev/null || true
    echo ".env file created! Please update with your settings."
fi

# Initialize database
echo "Initializing database..."
python -c "from models.database import Base, engine; Base.metadata.create_all(engine); print('Database initialized!')"
echo

deactivate
cd ..

# Setup Frontend
echo "[5/6] Setting up Frontend..."
cd frontend
if [ -d "node_modules" ]; then
    echo "node_modules already exists, skipping installation..."
else
    echo "Installing frontend dependencies..."
    npm install
fi
echo

# Create frontend .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cp .env.example .env 2>/dev/null || true
fi

cd ..

echo "[6/6] Setup Complete!"
echo
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo "1. Update backend/.env with your configuration"
echo "2. Update frontend/.env if needed"
echo "3. Run ./start.sh to launch the application"
echo
echo "To start the application manually:"
echo "  Backend:  cd backend && source venv/bin/activate && python -m uvicorn main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo
