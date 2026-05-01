# Main application entry point (RELOAD TRIGGER: manual restart)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from datetime import datetime

from routers import (
    users, listings, predictions_advanced as predictions, ar_customization,
    ar_customization_enhanced, google_auth, 
    messages, favorites, approvals, recommendations, analytics, ar_assets,
    support, notifications
)
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Exception logging middleware
@app.middleware("http")
async def log_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        with open("backend_error.log", "a") as f:
            f.write(f"\n--- {datetime.utcnow()} ---\n")
            f.write(f"Path: {request.url.path}\n")
            f.write(traceback.format_exc())
            f.write("\n")
        raise e from None

# Add session middleware for OAuth (must be before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour session
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# Set all CORS enabled origins
# NOTE: "*" cannot be used together with allow_credentials=True (browsers block it).
# Instead we list explicit localhost origins PLUS a regex that covers every
# private-network IP (192.168.x.x / 10.x.x.x / 172.16-31.x.x) on any port,
# which allows phone-on-same-WiFi testing without hardcoding IPs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "https://ezsell-indol.vercel.app",
        "https://ezsell.vercel.app",
    ],
    # Covers 192.168.x.x, 10.x.x.x, 172.16-31.x.x on any port
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
        r"(:\d+)?"
        r"|https://ezsell-.*\.vercel\.app"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# The original static_path was 'data', but the new routes will use a 'static' directory.
# We keep the 'data' directory creation for backward compatibility or other uses if any.
(Path(__file__).parent / "data").mkdir(exist_ok=True)

# Create directories if they don't exist
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(exist_ok=True)
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)

# Mount static and uploads directories
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Ensure the AR models sub-directory exists
ar_models_path = uploads_path / "ar_models"
ar_models_path.mkdir(exist_ok=True)

# Include routers
app.include_router(users.router, prefix=settings.API_V1_STR, tags=["Users"])
app.include_router(google_auth.router, prefix=settings.API_V1_STR, tags=["Google OAuth"])
app.include_router(listings.router, prefix=settings.API_V1_STR, tags=["Listings"])
app.include_router(predictions.router, prefix=settings.API_V1_STR, tags=["Predictions"])
app.include_router(ar_customization.router, prefix=settings.API_V1_STR, tags=["AR Customization"])
app.include_router(ar_customization_enhanced.router, prefix=settings.API_V1_STR, tags=["AR Enhanced"])
app.include_router(support.router, prefix=settings.API_V1_STR + "/support", tags=["Support"])
app.include_router(messages.router, prefix=settings.API_V1_STR, tags=["Messages"])
app.include_router(favorites.router, prefix=settings.API_V1_STR, tags=["Favorites"])
app.include_router(approvals.router, prefix=settings.API_V1_STR, tags=["Approvals"])
app.include_router(recommendations.router, prefix=settings.API_V1_STR, tags=["Recommendations"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(notifications.router, prefix=settings.API_V1_STR, tags=["Notifications"])
app.include_router(ar_assets.router, prefix=settings.API_V1_STR, tags=["AR Assets"])

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
