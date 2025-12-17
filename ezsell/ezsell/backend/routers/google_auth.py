# Google OAuth authentication endpoints
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteConfig
from starlette.responses import RedirectResponse
from datetime import datetime
import traceback

from models.database import get_db, User
from core.config import settings
from core.security import create_access_token

router = APIRouter()

# Configure OAuth
config = StarletteConfig(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
})

oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/auth/google/test")
async def test_google_config():
    """Test endpoint to verify Google OAuth configuration"""
    return {
        "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(settings.GOOGLE_CLIENT_SECRET),
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "oauth_registered": oauth.google is not None
    }

@router.get("/auth/google/login")
async def google_login(request: Request):
    """
    Redirect to Google OAuth login page
    """
    print(f"=== Google OAuth Login Started ===")
    print(f"Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback
    - Get user info from Google
    - Check if user exists in database
    - If exists: update last_login and return token
    - If not exists: create new user and return token
    """
    try:
        print("=== Google OAuth Callback Started ===")
        print(f"Request URL: {request.url}")
        print(f"Query params: {dict(request.query_params)}")
        
        # Get authorization token from Google with leeway for clock skew
        try:
            # Add leeway parameter to handle clock synchronization issues
            token = await oauth.google.authorize_access_token(request, leeway=120)
            print(f"Token received successfully")
        except Exception as token_error:
            print(f"Error getting token: {str(token_error)}")
            raise
        
        # Get user info from Google
        user_info = token.get('userinfo')
        print(f"User info received: {user_info is not None}")
        if user_info:
            print(f"User email: {user_info.get('email')}")
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        full_name = user_info.get('name')
        avatar_url = user_info.get('picture')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Check if user exists by Google ID first (prevents duplicates)
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Check if email exists (user might have signed up with email/password)
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Link Google account to existing user account
                user.google_id = google_id
                user.auth_provider = "google"
                user.full_name = full_name or user.full_name  # Update name if provided
                user.avatar_url = avatar_url or user.avatar_url
                user.is_verified = True  # Mark as verified since Google verified
            else:
                # Create new user with Google account
                username = email.split('@')[0]  # Use email prefix as username
                
                # Ensure username is unique to prevent duplicates
                counter = 1
                original_username = username
                while db.query(User).filter(User.username == username).first():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    google_id=google_id,
                    auth_provider="google",
                    is_verified=True,  # Google accounts are pre-verified
                    hashed_password=None  # No password for Google OAuth users
                )
                db.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.username})
        
        print(f"User authenticated successfully: {user.username}")
        print(f"Redirecting to frontend with token")
        
        # Redirect to frontend callback with token
        frontend_callback_url = f"http://localhost:8080/auth/google/callback?token={access_token}"
        return RedirectResponse(url=frontend_callback_url, status_code=302)
        
    except Exception as e:
        print(f"Google OAuth Error: {str(e)}")
        traceback.print_exc()
        # Redirect to frontend with error
        error_message = str(e).replace(' ', '+')  # URL encode spaces
        frontend_callback_url = f"http://localhost:8080/auth/google/callback?error={error_message}"
        return RedirectResponse(url=frontend_callback_url, status_code=302)

@router.get("/auth/user")
def get_authenticated_user(request: Request, db: Session = Depends(get_db)):
    """
    Get current authenticated user info (for both local and Google auth)
    """
    # This endpoint can be used by frontend to get user data after OAuth
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from core.security import get_current_user
    # Implementation would use get_current_user dependency
    pass
