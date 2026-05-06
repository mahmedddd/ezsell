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
# --- CORS CONFIGURATION ---
@app.middleware("http")
async def cors_handler(request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import JSONResponse
        response = JSONResponse(content="OK")
    else:
        response = await call_next(request)
    
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept"
        response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response

# The original static_path was 'data', but the new routes will use a 'static' directory.
# We keep the 'data' directory creation for backward compatibility or other uses if any.
(Path(__file__).parent / "data").mkdir(exist_ok=True)

# Create directories if they don't exist
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(exist_ok=True)
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)

# Custom StaticFiles class to force CORS headers and enable efficient caching
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        # Enable browser caching for 24 hours to speed up repeated views
        # Still uses 'must-revalidate' to ensure the client checks with the server
        response.headers["Cache-Control"] = "public, max-age=86400, must-revalidate"
        return response

# Mount static and uploads directories with the CORS-enabled class
app.mount("/static", CORSStaticFiles(directory=static_path), name="static")
app.mount("/uploads", CORSStaticFiles(directory=uploads_path), name="uploads")

# Ensure the AR models sub-directory exists
ar_models_path = uploads_path / "ar_models"
ar_models_path.mkdir(exist_ok=True)

# Global Error Logger
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print(f"🔥 [GLOBAL_ERROR] {request.method} {request.url}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "msg": str(exc)}
    )

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
