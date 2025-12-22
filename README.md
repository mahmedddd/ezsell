# EZSell - AI-Powered Marketplace Platform

A modern marketplace platform with AI-powered price prediction, AR furniture visualization, and advanced product listings.

## 🚀 Features

- **AI Price Prediction**: Market-based pricing for mobiles, laptops, and furniture with 99%+ accuracy
- **AR Furniture Visualization**: Preview furniture in your room using AR technology
- **Smart Title Validation**: Ensures complete product information in listings
- **Google OAuth**: Secure authentication with Google
- **Real-time Messaging**: Chat with buyers/sellers
- **Advanced Search & Filters**: Find exactly what you need
- **Favorites & Recommendations**: Personalized experience

## 📋 Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mahmedddd/ezsell.git
cd ezsell
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd ezsell/ezsell/backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database
python create_tables.py

# Initialize database with sample data (optional)
# The database will be created automatically on first run
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Environment Variables

The project uses default configurations that work out of the box. No environment variables are required for local development.

## 🚀 Running the Application

### Option 1: Using Batch Files (Windows - Easiest)

**Backend:**
```bash
cd ezsell/ezsell/backend
start_backend.bat
```

**Frontend:**
```bash
cd ezsell/ezsell/frontend
start_frontend.bat
```

### Option 2: Manual Commands

**Backend:**
```bash
cd ezsell/ezsell/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd ezsell/ezsell/frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
ezsell/
├── ezsell/ezsell/
│   ├── backend/              # FastAPI backend
│   │   ├── main.py          # Application entry point
│   │   ├── requirements.txt # Python dependencies
│   │   ├── start_backend.bat # Quick start script
│   │   ├── create_tables.py # Database setup
│   │   ├── core/            # Core configurations
│   │   ├── models/          # Database models
│   │   ├── routers/         # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── ml_pipeline/     # ML models & training
│   │   ├── trained_models/  # Trained ML models
│   │   └── uploads/         # User uploads
│   │
│   └── frontend/            # React + Vite frontend
│       ├── src/             # Source code
│       │   ├── components/  # React components
│       │   ├── pages/       # Page components
│       │   └── lib/         # Utilities & API
│       ├── package.json     # Node dependencies
│       └── start_frontend.bat # Quick start script
│
└── README.md                # This file
```

## 🔑 Default Credentials

For testing, you can create a new account or use Google OAuth login.

## 📊 ML Models

The project includes pre-trained models for:
- **Mobile phones**: 164 models with 99.94% accuracy
- **Laptops**: 293 models with 92.29% accuracy  
- **Furniture**: All types with 99.96% accuracy

Models are located in `backend/trained_models/` and load automatically.

## 🧪 Testing

### Test Price Prediction

```bash
cd ezsell/ezsell/backend
python test_prediction.py
```

### Test ML Pipeline

```bash
python test_ml_pipeline.py
```

### Run Backend Tests

```bash
pytest
```

## 📝 API Endpoints

### Authentication
- `POST /api/v1/register` - User registration
- `POST /api/v1/login` - User login
- `GET /api/v1/auth/google` - Google OAuth

### Listings
- `GET /api/v1/listings` - Get all listings
- `POST /api/v1/listings` - Create listing
- `GET /api/v1/listings/{id}` - Get listing details
- `PUT /api/v1/listings/{id}` - Update listing
- `DELETE /api/v1/listings/{id}` - Delete listing

### Price Prediction
- `POST /api/v1/predict-price` - Get AI price prediction
- `GET /api/v1/dropdown-options/{category}` - Get form options
- `GET /api/v1/validate-title` - Validate listing title

### AR Features
- `GET /api/v1/furniture-items` - Get available furniture
- `POST /api/v1/ar-preview` - Generate AR preview

## 🛠️ Development

### Adding New Features

1. **Backend**: Add routes in `backend/routers/`
2. **Frontend**: Add components in `frontend/src/components/`
3. **Database**: Update models in `backend/models/database.py`

### Training New ML Models

```bash
cd ezsell/ezsell/backend
python run_enhanced_pipeline.py --category mobile
python run_enhanced_pipeline.py --category laptop
python run_enhanced_pipeline.py --category furniture
```

## 🐛 Troubleshooting

### Backend won't start
- Ensure Python 3.10+ is installed: `python --version`
- Check if port 8000 is free: `netstat -ano | findstr :8000`
- Install dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `npm install`
- Check if port 8080 is free

### Database errors
- Run: `python create_tables.py`
- Delete `ezsell.db` and recreate

### ML models not found
- Models are included in the repository
- If missing, run: `python run_enhanced_pipeline.py --category all`

## 📦 Deployment

### Backend Deployment

1. Set environment variables for production
2. Use a production WSGI server (Gunicorn)
3. Set up PostgreSQL database
4. Configure CORS for production domain

### Frontend Deployment

```bash
npm run build
# Deploy the 'dist' folder to your hosting service
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- **Ahmed** - Initial work - [mahmedddd](https://github.com/mahmedddd)

## 🙏 Acknowledgments

- FastAPI for the amazing backend framework
- React + Vite for the frontend
- Scikit-learn for ML capabilities
- Shadcn/ui for beautiful components

## 📞 Support

For support, email your-email@example.com or open an issue on GitHub.

---

Made with ❤️ by the EZSell Team
