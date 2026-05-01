# EZSell Backend - FastAPI

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Install dependencies:
```bash
venv\Scripts\pip install -r requirements.txt
```

3. Run the server:
```bash
venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Users
- `POST /api/v1/register` - Register new user
- `POST /api/v1/login` - Login user
- `GET /api/v1/me` - Get current user info
- `PATCH /api/v1/me` - Update profile

### Listings
- `GET /api/v1/listings` - Get all listings
- `POST /api/v1/listings` - Create listing
- `GET /api/v1/listings/{id}` - Get listing by ID
- `PUT /api/v1/listings/{id}` - Update listing
- `DELETE /api/v1/listings/{id}` - Delete listing
- `GET /api/v1/my-listings` - Get user's listings

### Price Prediction
- `POST /api/v1/predict-price` - Predict item price
- `GET /api/v1/prediction-features/{category}` - Get required features

### AR Customization
- `POST /api/v1/ar-preview` - Generate AR preview
- `GET /api/v1/furniture-items` - Get available furniture

## Database

SQLite database will be created automatically at `ezsell.db`
