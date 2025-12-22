# EZSell - Complete Setup Guide

This guide will help you set up the entire EZSell project on any machine.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

## Quick Setup

### Windows

1. Clone the repository:
```bash
git clone https://github.com/mahmedddd/ezsell.git
cd ezsell/ezsell
```

2. Run the setup script:
```bash
setup.bat
```

3. Start the application:
```bash
start.bat
```

### Linux/Mac

1. Clone the repository:
```bash
git clone https://github.com/mahmedddd/ezsell.git
cd ezsell/ezsell
```

2. Make scripts executable:
```bash
chmod +x setup.sh start.sh
```

3. Run the setup script:
```bash
./setup.sh
```

4. Start the application:
```bash
./start.sh
```

## What the Setup Does

1. ✅ Checks Python and Node.js installation
2. ✅ Creates a Python virtual environment
3. ✅ Installs all backend dependencies
4. ✅ Installs all frontend dependencies
5. ✅ Creates .env configuration files
6. ✅ Initializes the database

## Manual Setup (Alternative)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Initialize database
python -c "from models.database import Base, engine; Base.metadata.create_all(engine)"
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

## Running the Application

### Using Scripts (Recommended)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Manual Start

**Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Configuration

### Backend (.env)

Edit `backend/.env`:
```env
# Database
DATABASE_URL=sqlite:///./ezsell.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Frontend (.env)

Edit `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Testing the Setup

1. **Test Backend**:
   - Open: http://localhost:8000/docs
   - You should see the API documentation

2. **Test Frontend**:
   - Open: http://localhost:8080
   - You should see the EZSell homepage

3. **Create Test Account**:
   - Go to http://localhost:8080/register
   - Create an account and log in

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

**Backend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (port 8080):**
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8080 | xargs kill -9
```

### Python Module Not Found

Make sure you're in the virtual environment:
```bash
# Check if activated (you should see (venv) in your terminal)
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### npm install fails

Try clearing cache:
```bash
cd frontend
rm -rf node_modules package-lock.json  # Linux/Mac
# or
rmdir /s node_modules  # Windows
del package-lock.json  # Windows

npm install
```

### Database Issues

Reset the database:
```bash
cd backend
rm ezsell.db  # Delete old database
python -c "from models.database import Base, engine; Base.metadata.create_all(engine)"
```

## Project Structure

```
ezsell/
├── backend/              # FastAPI Backend
│   ├── venv/            # Virtual environment (created by setup)
│   ├── models/          # Database models
│   ├── routers/         # API endpoints
│   ├── schemas/         # Pydantic schemas
│   ├── core/            # Security, config
│   ├── ml_pipeline/     # ML models
│   ├── requirements.txt # Python dependencies
│   └── main.py          # FastAPI app
├── frontend/            # React + Vite Frontend
│   ├── node_modules/    # npm packages (created by setup)
│   ├── src/             # React components
│   ├── package.json     # npm dependencies
│   └── vite.config.ts   # Vite configuration
├── setup.bat            # Windows setup script
├── setup.sh             # Linux/Mac setup script
├── start.bat            # Windows start script
└── start.sh             # Linux/Mac start script
```

## Additional Features

### ML Models

The ML models for price prediction are pre-trained and included. To retrain:

```bash
cd backend
python run_enhanced_pipeline.py --category mobile
python run_enhanced_pipeline.py --category laptop
python run_enhanced_pipeline.py --category furniture
```

### Admin Panel

Access the admin features by registering as the first user or manually setting `is_admin=True` in the database.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the error messages in the terminal
- Check that all prerequisites are installed correctly
- Ensure you're running commands from the correct directory

## Environment Variables Reference

### Backend Required
- `SECRET_KEY`: JWT secret (auto-generated if not set)
- `DATABASE_URL`: Database connection string

### Backend Optional
- `SMTP_*`: Email configuration
- `GOOGLE_*`: OAuth configuration
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (default: 30)

### Frontend
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000/api/v1)

## Development Tips

1. **Hot Reload**: Both servers support hot reload - changes will auto-refresh
2. **API Testing**: Use http://localhost:8000/docs for interactive API testing
3. **Database Inspection**: Use DB Browser for SQLite to inspect the database
4. **Logs**: Check terminal windows for error messages

---

**Need Help?** Make sure all prerequisites are installed and scripts are run from the project root directory.
