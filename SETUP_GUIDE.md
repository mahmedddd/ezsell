# Complete Setup Guide for EZSell

This guide will help you set up EZSell from scratch on a fresh machine.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installing Prerequisites](#installing-prerequisites)
3. [Project Setup](#project-setup)
4. [Running the Application](#running-the-application)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for initial setup

### Software Requirements
- Python 3.10 or higher
- Node.js 18 or higher
- Git

## Installing Prerequisites

### Step 1: Install Python

#### Windows:
1. Download Python from https://www.python.org/downloads/
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:
   ```bash
   python --version
   ```

#### macOS:
```bash
brew install python@3.10
```

#### Linux:
```bash
sudo apt update
sudo apt install python3.10 python3-pip
```

### Step 2: Install Node.js

#### Windows:
1. Download from https://nodejs.org/
2. Run installer with default settings
3. Verify installation:
   ```bash
   node --version
   npm --version
   ```

#### macOS:
```bash
brew install node
```

#### Linux:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 3: Install Git

#### Windows:
1. Download from https://git-scm.com/
2. Run installer with default settings

#### macOS:
```bash
brew install git
```

#### Linux:
```bash
sudo apt install git
```

## Project Setup

### Step 1: Clone Repository

```bash
# Clone the project
git clone https://github.com/mahmedddd/ezsell.git

# Navigate to project directory
cd ezsell
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd ezsell/ezsell/backend

# Create virtual environment (RECOMMENDED)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create database tables
python create_tables.py
```

**Expected Output:**
```
✅ Database tables created successfully!
✅ Sample data inserted (optional)
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend (from backend directory)
cd ../frontend

# Install Node.js dependencies
npm install
```

**Expected Output:**
```
added XXX packages in XXs
```

## Running the Application

### Method 1: Using Batch Scripts (Windows - Easiest!)

#### Start Backend:
```bash
cd ezsell/ezsell/backend
# Double-click start_backend.bat
# OR run in terminal:
start_backend.bat
```

#### Start Frontend:
```bash
cd ezsell/ezsell/frontend
# Double-click start_frontend.bat
# OR run in terminal:
start_frontend.bat
```

### Method 2: Manual Commands

#### Terminal 1 - Backend:
```bash
cd ezsell/ezsell/backend

# Activate virtual environment if you created one
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2 - Frontend:
```bash
cd ezsell/ezsell/frontend

# Start frontend development server
npm run dev
```

**Expected Output:**
```
VITE v5.4.19  ready in XXX ms

➜  Local:   http://localhost:8080/
➜  Network: http://192.168.x.x:8080/
```

## Verification

### 1. Check Backend

Open your browser and visit:
- http://localhost:8000 - Should show welcome message
- http://localhost:8000/docs - Should show API documentation

### 2. Check Frontend

Open your browser and visit:
- http://localhost:8080 - Should show EZSell homepage

### 3. Test Complete Flow

1. **Register Account**:
   - Go to http://localhost:8080
   - Click "Sign Up" or "Register"
   - Create a new account

2. **Login**:
   - Login with your credentials
   - You should see the dashboard

3. **Create Listing**:
   - Click "Create Listing"
   - Fill in the form
   - Upload an image
   - Submit

4. **View Listings**:
   - Go to listings page
   - You should see your created listing

## Troubleshooting

### Problem: "Python not found"
**Solution:**
- Reinstall Python and check "Add to PATH"
- Restart terminal/command prompt
- Verify: `python --version`

### Problem: "pip not found"
**Solution:**
```bash
python -m ensurepip --upgrade
```

### Problem: "Port 8000 already in use"
**Solution:**
```bash
# Windows:
netstat -ano | findstr :8000
# Kill the process using the PID
taskkill /PID <PID> /F

# Linux/macOS:
lsof -ti:8000 | xargs kill -9
```

### Problem: "Port 8080 already in use"
**Solution:**
- Frontend will automatically try port 8081, 8082, etc.
- Or manually kill the process:
```bash
# Windows:
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/macOS:
lsof -ti:8080 | xargs kill -9
```

### Problem: "Module not found" errors
**Solution:**
```bash
# Backend:
cd ezsell/ezsell/backend
pip install -r requirements.txt

# Frontend:
cd ezsell/ezsell/frontend
rm -rf node_modules
npm install
```

### Problem: Database errors
**Solution:**
```bash
cd ezsell/ezsell/backend
# Delete old database
rm ezsell.db
# Recreate tables
python create_tables.py
```

### Problem: Frontend won't build
**Solution:**
```bash
cd ezsell/ezsell/frontend
# Clear cache
rm -rf node_modules
rm -rf .vite
npm cache clean --force
npm install
npm run dev
```

### Problem: ML models not loading
**Solution:**
```bash
cd ezsell/ezsell/backend
# Models are included in the repository
# If missing, train them:
python run_enhanced_pipeline.py --category mobile
python run_enhanced_pipeline.py --category laptop
python run_enhanced_pipeline.py --category furniture
```

## Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Database created
- [ ] Backend running on port 8000
- [ ] Frontend running on port 8080
- [ ] Can access http://localhost:8080
- [ ] Can create account and login

## Next Steps

After successful setup:

1. **Explore Features**: Try creating listings, searching, messaging
2. **Test AR**: Create furniture listings and use AR preview
3. **Test Price Prediction**: Create listings and see AI predictions
4. **Read API Docs**: Visit http://localhost:8000/docs
5. **Customize**: Modify code and see changes in real-time

## Getting Help

If you encounter issues not covered here:

1. Check the main README.md
2. Look at existing documentation in `/backend/*.md`
3. Open an issue on GitHub
4. Check the API documentation at http://localhost:8000/docs

## Production Deployment

For production deployment:

1. **Backend**:
   - Use PostgreSQL instead of SQLite
   - Set up environment variables
   - Use Gunicorn/uvicorn workers
   - Set up HTTPS
   - Configure CORS properly

2. **Frontend**:
   - Build: `npm run build`
   - Deploy `dist` folder to hosting
   - Update API URLs in production

3. **Both**:
   - Set up proper logging
   - Configure monitoring
   - Set up backups
   - Use environment variables for secrets

---

**Happy Coding! 🚀**
