#!/bin/bash
# EZSell Quick Setup Script for Linux/macOS
# Run this script to set up the entire project

set -e  # Exit on error

echo "🚀 EZSell Setup Script"
echo "===================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d" " -f2)
echo "✅ Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install npm."
    exit 1
fi

echo "✅ npm $(npm --version) found"
echo ""

# Backend Setup
echo "📦 Setting up Backend..."
cd ezsell/ezsell/backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "  Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "  Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create database
echo "  Creating database..."
python create_tables.py

# Copy environment file
if [ ! -f ".env" ]; then
    echo "  Creating .env file..."
    cp .env.example .env
fi

echo "✅ Backend setup complete!"
echo ""

# Frontend Setup
echo "📦 Setting up Frontend..."
cd ../frontend

# Install dependencies
echo "  Installing Node.js dependencies..."
npm install --silent

# Copy environment file
if [ ! -f ".env" ]; then
    echo "  Creating .env file..."
    cp .env.example .env
fi

echo "✅ Frontend setup complete!"
echo ""

# Success message
echo "🎉 Setup Complete!"
echo ""
echo "To start the application:"
echo ""
echo "Backend:"
echo "  cd ezsell/ezsell/backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Frontend:"
echo "  cd ezsell/ezsell/frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:8080"
echo ""
