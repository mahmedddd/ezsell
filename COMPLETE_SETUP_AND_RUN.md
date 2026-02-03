# EZSell Complete Setup and Run Guide

> **IMPORTANT**: This is the ONLY setup guide you need. Follow these steps sequentially for a complete working setup.

## 🔧 System Requirements

### Critical Version Requirements
- **Python 3.10.x** (NOT 3.14 or higher - compatibility issues with dependencies)
- **Node.js 16.x or higher**
- **npm 8.x or higher**
- **Windows 10/11** (tested on Windows)

### Check Your Python Version
```powershell
py -3.10 --version
# Should output: Python 3.10.x
```

If Python 3.10 is not installed, download from: https://www.python.org/downloads/

---

## 📦 Complete Setup (One-Time)

### Step 1: Clone Repository
```powershell
git clone <your-repo-url>
cd ezsell
```

### Step 2: Create Python Virtual Environment (Python 3.10)
```powershell
# Create venv with Python 3.10 specifically
py -3.10 -m venv .venv

# Activate venv
.venv\Scripts\activate

# Verify Python version
python --version  # Should show 3.10.x
```

### Step 3: Install Backend Dependencies
```powershell
cd ezsell\ezsell\backend

# Upgrade pip first
python -m pip install --upgrade pip

# Install all backend dependencies
pip install fastapi uvicorn sqlalchemy bcrypt python-jose python-multipart aiosmtplib pydantic pydantic-settings xgboost lightgbm "scikit-learn>=1.0,<1.8" pandas numpy pillow opencv-python-headless requests python-dotenv email-validator Authlib httpx itsdangerous
```

### Step 4: Create Backend Environment File
Create `ezsell\ezsell\backend\.env` with this content:

```env
# EZSell Backend Environment Variables

# Application
PROJECT_NAME=EZSell FastAPI
PROJECT_VERSION=1.0.0
API_V1_STR=/api/v1

# Security
SECRET_KEY=ezsell-development-secret-key-change-in-production-12345678
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Database
DATABASE_URL=sqlite:///./ezsell.db

# Google OAuth (Optional - leave empty if not configured)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Email Configuration (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:8080

# File Upload
MAX_UPLOAD_SIZE=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp

# ML Models
MODEL_PATH=./models_enhanced
ENABLE_PRICE_PREDICTION=true

# AR Features
AR_ENABLED=true
AR_PREVIEW_PATH=./data/ar_previews

# Development
DEBUG=true
RELOAD=true
```

**Email Setup Notes:**
- Use Gmail App Password (not your regular password)
- Generate at: https://myaccount.google.com/apppasswords
- 16-character password with no spaces

### Step 5: Initialize Database
```powershell
# From backend directory
python create_tables.py
```

### Step 6: Install Frontend Dependencies
```powershell
cd ..\frontend

# Install with legacy peer deps flag (required for React 18 compatibility)
npm install --legacy-peer-deps
```

### Step 7: Create Frontend Environment File
Create `ezsell\ezsell\frontend\.env` with this content:

```env
# Frontend Environment Variables
VITE_API_URL=http://localhost:8000/api/v1
VITE_ENABLE_AR=true
VITE_ENABLE_ANALYTICS=true
```

---

## 🚀 Running the Application

### Every Time You Want to Run the App:

#### Terminal 1: Start Backend
```powershell
# Activate venv (if not already activated)
.venv\Scripts\activate

# Navigate to backend
cd ezsell\ezsell\backend

# Start backend server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend will be available at:** http://localhost:8000
**API Documentation:** http://localhost:8000/docs

#### Terminal 2: Start Frontend
```powershell
# Navigate to frontend
cd ezsell\ezsell\frontend

# Start frontend dev server
npm run dev
```

**Frontend will be available at:** http://localhost:8080

---

## 🎯 Module Configuration Status

All modules are configured and ready to use:

### ✅ Authentication & Authorization
- JWT token-based authentication (8-day expiration)
- Email verification with 6-digit codes (2-minute expiration)
- Google OAuth (optional, configure credentials in .env)
- Password hashing with bcrypt

### ✅ Price Prediction (AI Module)
- **Mobile**: XGBoost + LightGBM ensemble (99.95% accuracy)
- **Laptop**: XGBoost + LightGBM ensemble (~98% accuracy)
- **Furniture**: XGBoost + LightGBM ensemble (99.50% accuracy)
- Location: `backend/models_enhanced/`
- Files: `mobile_predictor.pkl`, `laptop_predictor.pkl`, `furniture_predictor.pkl`

### ✅ Recommendation System
- TF-IDF based similarity matching
- User behavior tracking
- Category-based filtering
- Endpoint: `/api/v1/recommendations/{listing_id}`

### ✅ Analytics Module
- User activity tracking
- Listing performance metrics
- Search analytics
- Dashboard: `/analytics`

### ✅ AR Furniture Preview
- 3D model support
- Real-time preview generation
- Endpoint: `/api/v1/ar-preview-enhanced`

### ✅ Regex Ad Posting
- Automatic title validation
- Content moderation
- Category-specific validation
- Endpoint: `/api/v1/validate-title`

---

## 📝 API Endpoints Overview

### Authentication
- `POST /api/v1/register` - Register new user
- `POST /api/v1/send-verification-code` - Send email verification
- `POST /api/v1/verify-code` - Verify email code
- `POST /api/v1/login` - Login user
- `GET /api/v1/me` - Get current user

### Listings
- `GET /api/v1/listings` - Get all listings (with filters)
- `POST /api/v1/listings` - Create listing (multipart/form-data)
- `GET /api/v1/listings/{id}` - Get single listing
- `PUT /api/v1/listings/{id}` - Update listing
- `DELETE /api/v1/listings/{id}` - Delete listing

### Price Prediction
- `POST /api/v1/predict-price` - Get AI price prediction
- `POST /api/v1/predict-price-with-dropdowns` - Predict with dropdown data

### Recommendations
- `GET /api/v1/recommendations/{listing_id}` - Get similar listings

### Analytics
- `GET /api/v1/analytics/user-activity` - User activity stats
- `GET /api/v1/analytics/listing-performance` - Listing metrics

### AR Preview
- `POST /api/v1/ar-preview-enhanced` - Generate AR preview

---

## 🐛 Common Issues & Solutions

### Issue 1: Backend Crashes on Request
**Symptom:** Server starts but crashes when receiving HTTP requests

**Solution:** You're using Python 3.14 (incompatible)
```powershell
# Remove old venv
Remove-Item .venv -Recurse -Force

# Create new venv with Python 3.10
py -3.10 -m venv .venv
.venv\Scripts\activate

# Reinstall dependencies
cd ezsell\ezsell\backend
pip install fastapi uvicorn sqlalchemy bcrypt python-jose python-multipart aiosmtplib pydantic pydantic-settings xgboost lightgbm "scikit-learn>=1.0,<1.8" pandas numpy pillow opencv-python-headless requests python-dotenv email-validator Authlib httpx itsdangerous
```

### Issue 2: Frontend Build Errors
**Symptom:** npm install fails or build errors

**Solution:** Use legacy peer deps flag
```powershell
npm install --legacy-peer-deps
```

### Issue 3: Email Verification Not Working
**Symptom:** 500 error when sending verification code

**Solution:** 
1. Use Gmail App Password (not regular password)
2. Ensure no spaces in password
3. Restart backend after updating .env

### Issue 4: Database Connection Error
**Symptom:** "no such table" errors

**Solution:** Run database initialization
```powershell
cd ezsell\ezsell\backend
python create_tables.py
```

### Issue 5: CORS Errors
**Symptom:** Frontend can't connect to backend

**Solution:** Backend must run on 0.0.0.0:8000, frontend on localhost:8080

### Issue 6: Image Upload Fails
**Symptom:** "Validation Error" when creating listing

**Solution:** Minimum 2 images required (not 5). Form data must be sent as multipart/form-data.

---

## 🔥 Quick Start (TL;DR)

```powershell
# 1. Setup (one time)
py -3.10 -m venv .venv
.venv\Scripts\activate
cd ezsell\ezsell\backend
pip install fastapi uvicorn sqlalchemy bcrypt python-jose python-multipart aiosmtplib pydantic pydantic-settings xgboost lightgbm "scikit-learn>=1.0,<1.8" pandas numpy pillow opencv-python-headless requests python-dotenv email-validator Authlib httpx itsdangerous
python create_tables.py
cd ..\frontend
npm install --legacy-peer-deps

# 2. Create .env files (see Step 4 & 7 above)

# 3. Run backend (Terminal 1)
.venv\Scripts\activate
cd ezsell\ezsell\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Run frontend (Terminal 2)
cd ezsell\ezsell\frontend
npm run dev
```

**Access:** http://localhost:8080

---

## 📊 Testing the Setup

### 1. Test Backend
Open http://localhost:8000/docs - Should see Swagger UI

### 2. Test Frontend
Open http://localhost:8080 - Should see homepage

### 3. Test Complete Flow
1. Sign up with email verification
2. Login
3. Create a listing (minimum 2 images)
4. View price prediction
5. Check recommendations
6. Browse listings

---

## 🎓 Architecture Overview

```
ezsell/
├── .venv/                          # Python 3.10 virtual environment
├── ezsell/ezsell/
│   ├── backend/                    # FastAPI backend
│   │   ├── main.py                 # Entry point
│   │   ├── .env                    # Backend config
│   │   ├── models_enhanced/        # ML models (.pkl files)
│   │   ├── core/                   # Core utilities
│   │   │   ├── config.py           # Settings
│   │   │   ├── security.py         # JWT auth
│   │   │   └── email_service.py    # Email sender
│   │   ├── routers/                # API endpoints
│   │   │   ├── users.py            # Auth endpoints
│   │   │   ├── listings.py         # Listing CRUD
│   │   │   ├── predictions_advanced.py  # Price prediction
│   │   │   ├── recommendations.py  # Recommendations
│   │   │   └── analytics.py        # Analytics
│   │   ├── models/                 # Database models
│   │   └── schemas/                # Pydantic schemas
│   └── frontend/                   # React frontend
│       ├── .env                    # Frontend config
│       ├── src/
│       │   ├── lib/
│       │   │   └── api.ts          # API client
│       │   ├── pages/              # Page components
│       │   └── components/         # Reusable components
│       └── package.json
└── COMPLETE_SETUP_AND_RUN.md       # This file
```

---

## 🔐 Security Notes

### Development vs Production

**Current Setup (Development):**
- SQLite database
- Debug mode enabled
- CORS allows localhost
- Simple secret key

**For Production:**
- Use PostgreSQL/MySQL
- Set DEBUG=false
- Update SECRET_KEY to strong random value
- Configure proper CORS origins
- Use HTTPS
- Set up proper firewall rules

---

## 📱 User Workflow

1. **Sign Up** → Email verification → Login
2. **Create Listing** → Upload images (min 2) → Get AI price prediction → Set price
3. **Browse Listings** → Filter by category/location → View details
4. **Recommendations** → See similar items based on views
5. **Analytics** → Track listing performance

---

## 💡 Tips

- Keep both terminals running while using the app
- Backend auto-reloads on code changes (--reload flag)
- Frontend auto-reloads via Vite HMR
- Check backend terminal for API logs
- Use browser DevTools Network tab for debugging

---

## 🆘 Need Help?

1. Check this guide first
2. Review "Common Issues & Solutions" section
3. Check backend logs in Terminal 1
4. Check frontend console in browser DevTools
5. Verify Python version: `python --version` (must be 3.10.x)
6. Verify all .env files are created correctly

---

## ✅ Verification Checklist

Before reporting issues, verify:

- [ ] Python 3.10.x installed and venv created
- [ ] All backend dependencies installed
- [ ] Backend .env file created with email credentials
- [ ] Database initialized (create_tables.py ran)
- [ ] Frontend dependencies installed with --legacy-peer-deps
- [ ] Frontend .env file created
- [ ] Backend running on port 8000
- [ ] Frontend running on port 8080
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:8080

---

**Last Updated:** February 2026
**Python Version:** 3.10.x (Required)
**Status:** ✅ All modules configured and tested
