#!/bin/bash
# Quick Setup Script for EZSell - One Command Setup
# Run: ./quick-setup.sh

set -e  # Exit on any error

echo ""
echo "============================================="
echo "   EZSell - Quick Setup Script"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 not found. Please install Python 3.10+${NC}"
    echo "Download from: https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}[OK] Python found:${NC} $(python3 --version)"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js not found. Please install Node.js 18+${NC}"
    echo "Download from: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}[OK] Node.js found:${NC} $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm not found. Please install npm.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] npm found:${NC} $(npm --version)"

echo ""
echo "============================================="
echo "   Setting up Backend..."
echo "============================================="

cd "$(dirname "$0")/ezsell/ezsell/backend"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}[OK] Virtual environment created${NC}"
else
    echo -e "${YELLOW}[INFO] Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
else
    echo -e "${YELLOW}[WARNING] requirements.txt not found, installing core packages...${NC}"
    pip install fastapi uvicorn sqlalchemy pydantic python-multipart --quiet
    pip install pandas numpy scikit-learn joblib --quiet
    pip install python-jose passlib bcrypt python-dotenv --quiet
    echo -e "${GREEN}[OK] Core packages installed${NC}"
fi

# Create database
echo "Setting up database..."
if [ -f "create_tables.py" ]; then
    python create_tables.py
elif [ -f "models/database.py" ]; then
    python -c "from models.database import Base, engine; Base.metadata.create_all(engine); print('Database created')"
fi
echo -e "${GREEN}[OK] Database setup complete${NC}"

# Create required directories
echo "Creating required directories..."
mkdir -p uploads/listings
mkdir -p data/ar_previews
mkdir -p scraped_data/mobile
mkdir -p scraped_data/laptop
mkdir -p scraped_data/furniture
mkdir -p models_enhanced
mkdir -p trained_models
echo -e "${GREEN}[OK] Directories created${NC}"

echo ""
echo "============================================="
echo "   Setting up Frontend..."
echo "============================================="

cd ../frontend

# Install frontend dependencies
echo "Installing frontend dependencies..."
if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}[OK] Frontend dependencies installed${NC}"
else
    echo -e "${RED}[ERROR] package.json not found in frontend directory${NC}"
    exit 1
fi

echo ""
echo "============================================="
echo "   ✅ Setup Complete!"
echo "============================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Backend (in one terminal):"
echo "   cd ezsell/ezsell/backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn main:app --reload --port 8000"
echo ""
echo "2. Frontend (in another terminal):"
echo "   cd ezsell/ezsell/frontend"
echo "   npm run dev"
echo ""
echo "3. Open browser to: http://localhost:8080"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
