# 🚨 Troubleshooting Guide for EZSell Setup

This guide helps you resolve common issues when cloning and setting up the EZSell project.

## 📋 Quick Checklist

Before starting, ensure you have:
- [ ] **Python 3.10 or higher** installed
- [ ] **Node.js 18 or higher** installed
- [ ] **Git** installed
- [ ] Stable internet connection

---

## 🔧 Common Issues & Solutions

### 1. Python Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'` or similar

**Solutions:**

```bash
# Navigate to backend directory
cd ezsell/ezsell/backend

# Create a fresh virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# If requirements.txt is missing or incomplete, install manually:
pip install fastapi uvicorn sqlalchemy pydantic python-multipart
pip install pandas numpy scikit-learn joblib
pip install python-jose passlib bcrypt python-dotenv
pip install requests beautifulsoup4
```

---

### 2. Database Not Found / Table Errors

**Error:** `no such table: users` or `OperationalError: no such table`

**Solution:**

```bash
cd ezsell/ezsell/backend

# Make sure you're in the backend directory
# Run the database creation script
python create_tables.py

# If create_tables.py doesn't exist, create it:
```

Create `create_tables.py`:
```python
from models.database import Base, engine

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
```

Then run:
```bash
python create_tables.py
```

---

### 3. Frontend Dependencies Issues

**Error:** `npm ERR!` or module not found errors

**Solutions:**

```bash
cd ezsell/ezsell/frontend

# Clear npm cache
npm cache clean --force

# Delete existing node_modules and lock file
rm -rf node_modules
rm package-lock.json
# Or on Windows:
rmdir /s /q node_modules
del package-lock.json

# Reinstall dependencies
npm install

# If using bun (alternative):
bun install
```

---

### 4. Port Already in Use

**Error:** `Error: listen EADDRINUSE: address already in use :::8000`

**Solutions:**

**Windows:**
```powershell
# Find and kill process on port 8000 (backend)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# For port 8080 (frontend)
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

Or use different ports:
```bash
# Backend on port 8001
python -m uvicorn main:app --reload --port 8001

# Frontend on port 3000
npm run dev -- --port 3000
```

---

### 5. ML Models Not Found

**Error:** `Model not found` or `FileNotFoundError: models_enhanced/`

**Solution:**

The ML models are not included in the repository due to size. You have two options:

**Option A: Download pre-trained models** (if available)
```bash
# Contact the repository owner for model files
# Place them in: backend/models_enhanced/
# And: backend/trained_models/
```

**Option B: Train models yourself**
```bash
cd ezsell/ezsell/backend

# Run the ML pipeline to train models
python run_enhanced_pipeline.py --category all

# This will create models in:
# - models_enhanced/
# - trained_models/
```

**Note:** Training requires scraped data in `backend/scraped_data/`

---

### 6. Google OAuth Not Working

**Error:** OAuth errors or login failures

**Solution:**

Google OAuth requires configuration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:8080`
   - `http://localhost:8080/auth/callback`

6. Create `.env` file in backend:
```bash
# backend/.env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=your-secret-key-for-jwt
```

---

### 7. Missing Scraped Data

**Error:** `FileNotFoundError: scraped_data/`

**Solution:**

```bash
cd ezsell/ezsell/backend

# Create required directories
mkdir -p scraped_data/mobile
mkdir -p scraped_data/laptop
mkdir -p scraped_data/furniture

# Option 1: Run scrapers (requires internet)
python scrape_olx_simple.py

# Option 2: Use sample data (for testing)
# The system will work without scraped data, but ML models won't be available
```

---

### 8. SQLite Database Locked

**Error:** `database is locked`

**Solutions:**

```bash
# Close all backend instances
# Delete the database and recreate
cd ezsell/ezsell/backend
rm ezsell.db  # or del ezsell.db on Windows
python create_tables.py
```

---

### 9. CORS Errors in Browser

**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**

Check that backend CORS settings include your frontend URL:

In `backend/main.py`, verify:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 10. Images Not Loading

**Error:** Images show as broken or 404

**Solution:**

```bash
cd ezsell/ezsell/backend

# Create uploads directory
mkdir -p uploads/listings
mkdir -p data/ar_previews

# Ensure correct permissions (Linux/Mac)
chmod -R 755 uploads/
chmod -R 755 data/
```

---

## 🐍 Python Version Issues

If you have multiple Python versions:

```bash
# Use specific Python version
python3.10 -m venv venv
# or
py -3.10 -m venv venv

# Verify version inside venv
python --version
```

---

## 📦 Complete Fresh Install

If nothing works, start completely fresh:

```bash
# 1. Delete the repository
cd ..
rm -rf ezsell  # or rmdir /s /q ezsell on Windows

# 2. Clone again
git clone https://github.com/mahmedddd/ezsell.git
cd ezsell

# 3. Backend setup
cd ezsell/ezsell/backend
python -m venv venv
# Activate venv (see above)
pip install --upgrade pip
pip install -r requirements.txt
python create_tables.py

# 4. Frontend setup
cd ../frontend
rm -rf node_modules package-lock.json
npm install

# 5. Start servers
# Backend: python -m uvicorn main:app --reload --port 8000
# Frontend: npm run dev
```

---

## 🆘 Still Having Issues?

1. **Check Python/Node versions:**
   ```bash
   python --version  # Should be 3.10+
   node --version    # Should be 18+
   ```

2. **Check you're in correct directory:**
   ```bash
   pwd  # or cd on Windows
   # Should show: .../ezsell/ezsell/backend or .../ezsell/ezsell/frontend
   ```

3. **Check virtual environment is activated:**
   - You should see `(venv)` in your terminal prompt

4. **Check logs:**
   - Backend: Look at terminal where uvicorn is running
   - Frontend: Look at browser console (F12)

5. **Create an issue on GitHub:**
   - Include: OS, Python version, Node version, full error message
   - Repository: https://github.com/mahmedddd/ezsell/issues

---

## ✅ Successful Setup Indicators

When everything is working:

- Backend terminal shows: `Uvicorn running on http://127.0.0.1:8000`
- Frontend terminal shows: `Local: http://localhost:8080/`
- Browser opens to login page without errors
- Can register/login with test user
- Backend API docs accessible at: http://localhost:8000/docs

---

## 📞 Need Help?

- **Repository:** https://github.com/mahmedddd/ezsell
- **Issues:** https://github.com/mahmedddd/ezsell/issues
- **Documentation:** See README.md files in each directory
