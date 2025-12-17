# User authentication and management endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import bcrypt

from models.database import get_db, User, EmailVerification, PasswordReset
from schemas.schemas import UserCreate, UserResponse, UserLogin, Token
from core.security import create_access_token, get_current_user
from core.email_service import email_service
from datetime import datetime, timedelta

router = APIRouter()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
    try:
        print(f"Verifying password - Plain password length: {len(plain_password)}")
        print(f"Hashed password from DB: {hashed_password[:50]}...")
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        print(f"Verification result: {result}")
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_current_admin_user(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify that the current user is an admin"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.post("/send-verification-code")
async def send_verification_code(request: dict, db: Session = Depends(get_db)):
    """
    Send verification code to email before registration
    - Validates email doesn't already exist
    - Generates 6-digit code
    - Sends email with code
    - Stores code in database (expires in 2 minutes)
    """
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if email already registered
    existing_user = get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate verification code
    code = email_service.generate_verification_code()
    
    # Send email
    email_sent = await email_service.send_verification_email(email, code)
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    # Store verification code in database (expires in 2 minutes)
    verification = EmailVerification(
        email=email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=2),
        is_used=False
    )
    db.add(verification)
    db.commit()
    
    return {"message": "Verification code sent to email", "email": email}

@router.post("/verify-code")
def verify_email_code(request: dict, db: Session = Depends(get_db)):
    """
    Verify the email code before allowing registration
    - Checks if code exists and matches
    - Checks if code is not expired
    - Checks if code hasn't been used
    """
    email = request.get("email")
    code = request.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code are required")
    
    # Find the most recent verification code for this email
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.code == code,
        EmailVerification.is_used == False
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not verification:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Check if expired
    if datetime.utcnow() > verification.expires_at:
        raise HTTPException(status_code=400, detail="Verification code expired")
    
    # Mark as used
    verification.is_used = True
    db.commit()
    
    return {"message": "Email verified successfully", "email": email}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    SIGNUP: Register a new user and add to database
    - Verifies email was verified through verification code flow (within last 5 minutes)
    - Checks if username already exists in database
    - Checks if email already exists in database
    - Hashes the password for security
    - Adds new user to Supabase database
    """
    # Verify that email was verified through the verification code flow recently (within 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    verified = db.query(EmailVerification).filter(
        EmailVerification.email == user.email,
        EmailVerification.is_used == True,
        EmailVerification.created_at >= five_minutes_ago
    ).first()
    
    # Check if there's an old verification that has expired
    old_verification = db.query(EmailVerification).filter(
        EmailVerification.email == user.email,
        EmailVerification.is_used == True,
        EmailVerification.created_at < five_minutes_ago
    ).first()
    
    if old_verification and not verified:
        raise HTTPException(status_code=400, detail="Verification session timeout. Please verify your email again.")
    
    if not verified:
        raise HTTPException(status_code=400, detail="Email must be verified before registration. Please verify your email first.")
    
    # Check if username exists in database
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists in database
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create new user in database
    print(f"Registration - hashing password of length: {len(user.password)}")
    hashed_password = get_password_hash(user.password)
    print(f"Registration - hashed password: {hashed_password[:50]}...")
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_verified=True  # Mark as verified since they completed email verification
    )
    db.add(db_user)  # Add to database
    db.commit()      # Save to Supabase
    db.refresh(db_user)
    
    # Clean up verification codes for this email after successful registration
    db.query(EmailVerification).filter(EmailVerification.email == user.email).delete()
    db.commit()
    
    return db_user

@router.get("/check-username/{username}")
def check_username_availability(username: str, db: Session = Depends(get_db)):
    """Check if username is available for registration"""
    user = get_user_by_username(db, username=username)
    return {
        "available": user is None,
        "username": username
    }

@router.post("/debug-password-test")
def debug_password_test(request: dict, db: Session = Depends(get_db)):
    """Debug endpoint to test password hashing - REMOVE IN PRODUCTION"""
    username = request.get("username")
    password = request.get("password")
    
    user = get_user_by_username(db, username=username)
    if not user:
        return {"error": "User not found"}
    
    # Test hashing the password and comparing
    new_hash = get_password_hash(password)
    verification = verify_password(password, user.hashed_password)
    
    return {
        "stored_hash": user.hashed_password[:50],
        "new_hash": new_hash[:50],
        "verification": verification,
        "password_length": len(password)
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    print(f"Login attempt for username: {user_credentials.username}")
    
    # Check if user exists in database
    user = get_user_by_username(db, username=user_credentials.username)
    
    if not user:
        print(f"User not found: {user_credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found: {user.username}, checking password...")
    
    # Compare password with hashed password in database
    if not verify_password(user_credentials.password, user.hashed_password):
        print("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Password verified successfully")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Update last_login timestamp in database
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})
    print(f"Login successful for {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current logged-in user information"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users", response_model=List[UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users (admin only endpoint)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    full_name: str = None,
    avatar_url: str = None,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name:
        user.full_name = full_name
    if avatar_url:
        user.avatar_url = avatar_url
    
    db.commit()
    db.refresh(user)
    return user

@router.post("/request-password-reset")
async def request_password_reset(request: dict, db: Session = Depends(get_db)):
    """
    Request password reset code
    - Validates email exists in database
    - Generates 6-digit code
    - Sends email with reset code
    - Stores code in database (expires in 1 minute)
    """
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if email exists
    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=400, detail="No account found with this email address")
    
    # Generate reset code
    code = email_service.generate_verification_code()
    
    # Send email
    email_sent = await email_service.send_password_reset_email(email, code)
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send reset email")
    
    # Store reset code in database (expires in 1 minute)
    reset = PasswordReset(
        email=email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=1),
        is_used=False
    )
    db.add(reset)
    db.commit()
    
    return {"message": "Password reset code sent to your email"}

@router.post("/verify-reset-code")
def verify_reset_code(request: dict, db: Session = Depends(get_db)):
    """
    Verify the password reset code
    - Checks if code exists and matches
    - Checks if code is not expired
    - Checks if code hasn't been used
    """
    email = request.get("email")
    code = request.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code are required")
    
    # Find the most recent reset code for this email
    reset = db.query(PasswordReset).filter(
        PasswordReset.email == email,
        PasswordReset.code == code,
        PasswordReset.is_used == False
    ).order_by(PasswordReset.created_at.desc()).first()
    
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Check if expired
    if datetime.utcnow() > reset.expires_at:
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    return {"message": "Code verified successfully", "email": email}

@router.post("/reset-password")
def reset_password(request: dict, db: Session = Depends(get_db)):
    """
    Reset password using verified code
    - Verifies code again
    - Updates user's password
    - Marks code as used
    """
    email = request.get("email")
    code = request.get("code")
    new_password = request.get("new_password")
    
    if not email or not code or not new_password:
        raise HTTPException(status_code=400, detail="Email, code, and new password are required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Find the reset code
    reset = db.query(PasswordReset).filter(
        PasswordReset.email == email,
        PasswordReset.code == code,
        PasswordReset.is_used == False
    ).order_by(PasswordReset.created_at.desc()).first()
    
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Check if expired
    if datetime.utcnow() > reset.expires_at:
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    # Get user and update password
    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    print(f"Password reset - Email: {email}, Username: {user.username}")
    print(f"Password reset - Old hash: {user.hashed_password[:50]}...")
    print(f"Password reset - New password length: {len(new_password)}")
    hashed_password = get_password_hash(new_password)
    print(f"Password reset - New hashed password: {hashed_password[:50]}...")
    
    # Update password
    user.hashed_password = hashed_password
    
    # Mark reset code as used
    reset.is_used = True
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    print(f"Password reset successful for user: {user.username}")
    print(f"Verified stored hash after commit: {user.hashed_password[:50]}...")
    
    # Clean up old reset codes for this email
    db.query(PasswordReset).filter(PasswordReset.email == email).delete()
    db.commit()
    
    return {"message": "Password reset successfully"}

# ============= ADMIN ENDPOINTS =============

@router.get("/admin/analytics")
def get_admin_analytics(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get analytics data for admin dashboard"""
    from models.database import Listing
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    total_listings = db.query(Listing).count()
    active_listings = db.query(Listing).filter(Listing.is_sold == False).count()
    sold_listings = db.query(Listing).filter(Listing.is_sold == True).count()
    
    # Recent users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = db.query(User).filter(User.created_at >= week_ago).count()
    
    # Recent listings (last 7 days)
    recent_listings = db.query(Listing).filter(Listing.created_at >= week_ago).count()
    
    # Category breakdown
    from sqlalchemy import func
    category_stats = db.query(
        Listing.category,
        func.count(Listing.id).label('count')
    ).group_by(Listing.category).all()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "recent": recent_users
        },
        "listings": {
            "total": total_listings,
            "active": active_listings,
            "sold": sold_listings,
            "recent": recent_listings
        },
        "categories": [{"name": cat, "count": count} for cat, count in category_stats]
    }

@router.get("/admin/users", response_model=List[UserResponse])
def get_all_users_admin(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users with optional search (admin only)"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.delete("/admin/users/{user_id}")
def delete_user_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin and user.id != admin_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete other admin users")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}

@router.patch("/admin/users/{user_id}/toggle-active")
def toggle_user_active_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return {"message": f"User {user.username} is now {'active' if user.is_active else 'inactive'}", "is_active": user.is_active}
