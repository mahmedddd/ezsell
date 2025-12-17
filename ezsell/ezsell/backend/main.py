# Main application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from routers import users, listings, predictions, ar_customization, google_auth, messages, favorites, approvals
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add session middleware for OAuth (must be before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour session
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8081", "http://localhost:3000", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for AR previews
static_path = Path(__file__).parent / "data"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount uploads directory for user-uploaded images
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Include routers
app.include_router(users.router, prefix=settings.API_V1_STR, tags=["Users"])
app.include_router(google_auth.router, prefix=settings.API_V1_STR, tags=["Google OAuth"])
app.include_router(listings.router, prefix=settings.API_V1_STR, tags=["Listings"])
app.include_router(predictions.router, prefix=settings.API_V1_STR, tags=["Predictions"])
app.include_router(ar_customization.router, prefix=settings.API_V1_STR, tags=["AR Customization"])
app.include_router(messages.router, prefix=settings.API_V1_STR, tags=["Messages"])
app.include_router(favorites.router, prefix=settings.API_V1_STR, tags=["Favorites"])
app.include_router(approvals.router, prefix=settings.API_V1_STR, tags=["Approvals"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the EZSell API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
