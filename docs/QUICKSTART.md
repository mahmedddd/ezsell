# Quick Start - EZSell

The absolute fastest way to get EZSell running!

## Windows Users (Easiest!)

### 1. One-Click Setup
Double-click `setup.bat` in the project root, and wait for it to complete.

### 2. Start the Application
After setup completes:
1. Double-click `ezsell/ezsell/backend/start_backend.bat`
2. Double-click `ezsell/ezsell/frontend/start_frontend.bat`
3. Open http://localhost:8080 in your browser

**That's it!** 🎉

## Linux/macOS Users

### 1. Quick Setup
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Start Backend
```bash
cd ezsell/ezsell/backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend (in new terminal)
```bash
cd ezsell/ezsell/frontend
npm run dev
```

### 4. Open Application
Open http://localhost:8080 in your browser

## Manual Setup (All Platforms)

If automated scripts don't work:

### Prerequisites
1. Install Python 3.10+: https://www.python.org/downloads/
2. Install Node.js 18+: https://nodejs.org/
3. Install Git: https://git-scm.com/

### Backend Setup
```bash
cd ezsell/ezsell/backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python create_tables.py
```

### Frontend Setup
```bash
cd ezsell/ezsell/frontend
npm install
```

### Start Servers
Backend:
```bash
cd ezsell/ezsell/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (new terminal):
```bash
cd ezsell/ezsell/frontend
npm run dev
```

## Troubleshooting

### "Python not found"
- Download and install Python from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Restart your terminal/command prompt

### "Node not found"
- Download and install Node.js from https://nodejs.org/
- Restart your terminal/command prompt

### "Port already in use"
Kill the process and try again:
- Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
- Linux/Mac: `lsof -ti:8000 | xargs kill -9`

### Database errors
```bash
cd ezsell/ezsell/backend
rm ezsell.db  # Delete old database
python create_tables.py  # Recreate
```

## What's Included

✅ Backend API (FastAPI)
✅ Frontend UI (React + Vite)
✅ Pre-trained ML models
✅ Sample database structure
✅ All dependencies configured
✅ Ready to use!

## Next Steps

1. Create an account at http://localhost:8080
2. Create your first listing
3. Test price prediction
4. Explore AR features (for furniture)

## Need More Help?

- See [README.md](README.md) for full documentation
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

---

**Made with ❤️ by the EZSell Team**
