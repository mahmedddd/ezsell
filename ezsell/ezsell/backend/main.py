# Main application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from routers import (
    users, listings, predictions_advanced as predictions, ar_customization,
    ar_customization_enhanced, google_auth, 
    messages, favorites, approvals, recommendations, analytics, ar_assets
)
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
    ],
    # Covers 192.168.x.x, 10.x.x.x, 172.16-31.x.x on any port
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
        r":\d+"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Explicit CORS headers for static-file paths (/uploads/, /static/).
# FastAPI's CORSMiddleware covers API routes but StaticFiles responses may be
# served from the mount before the middleware injects headers in some Starlette
# versions.  This middleware guarantees CORS on every image response so that
# the frontend fetch()-based canvas loader (loadImageSafe) always succeeds.
@app.middleware("http")
async def add_cors_for_static_files(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/uploads/") or path.startswith("/static/"):
        origin = request.headers.get("origin", "")
        if origin:
            response.headers["access-control-allow-origin"] = origin
            response.headers["access-control-allow-credentials"] = "true"
        else:
            response.headers["access-control-allow-origin"] = "*"
        response.headers["cross-origin-resource-policy"] = "cross-origin"
    return response

# Mount static files directory for AR previews
static_path = Path(__file__).parent / "data"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount uploads directory for user-uploaded images
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

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
app.include_router(messages.router, prefix=settings.API_V1_STR, tags=["Messages"])
app.include_router(favorites.router, prefix=settings.API_V1_STR, tags=["Favorites"])
app.include_router(approvals.router, prefix=settings.API_V1_STR, tags=["Approvals"])
app.include_router(recommendations.router, tags=["Recommendations"])
app.include_router(analytics.router, tags=["Analytics"])
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
