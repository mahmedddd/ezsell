"""
Database models and connection setup
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from core.config import settings

# Database setup
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Handling SSL requirement for Postgres (like Supabase/Render)
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    # Render and Supabase often require SSL
    connect_args = {"sslmode": "require"}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    google_id = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    auth_provider = Column(String, default="local")

    # Relationships
    listings = relationship("Listing", back_populates="owner")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    favorites = relationship("Favorite", back_populates="user")

class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    category = Column(String)
    brand = Column(String, nullable=True)
    condition = Column(String)
    location = Column(String, nullable=True)
    images = Column(Text)  # JSON array of image paths
    # Furniture-specific fields
    furniture_type = Column(String, nullable=True)  # sofa, bed, table, chair, etc.
    material = Column(String, nullable=True)  # wood, metal, fabric, leather, etc.
    furniture_subtype = Column(String, nullable=True)  # e.g. "3_door", "4_door", "sliding", "L_shape"
    # Furniture enhancements
    furniture_brand = Column(String, nullable=True)
    is_sliding_door = Column(Boolean, default=False)
    has_mattress = Column(Boolean, default=False)
    mattress_type = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)
    is_sold = Column(Boolean, default=False)
    approval_status = Column(String, default="approved")  # "pending", "approved", "rejected"
    predicted_price = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    ar_model_url = Column(String, nullable=True)
    views = Column(Integer, default=0)  # Track listing views
    # ── AR 3-D Asset fields ──────────────────────────────────────────────────
    model_glb_url   = Column(String, nullable=True)   # Optimised GLB (Android/WebXR)
    model_usdz_url  = Column(String, nullable=True)   # USDZ (iOS AR QuickLook)
    dimensions_cm   = Column(Text, nullable=True)     # JSON: {"l":int,"w":int,"h":int}
    polygon_count   = Column(Integer, nullable=True)  # For LOD / perf gating
    
    # ── Fraud Prevention fields ──────────────────────────────────────────────
    listing_hash    = Column(String, index=True, nullable=True) # Hash of title+desc+price+owner
    image_hash      = Column(String, index=True, nullable=True) # Perceptual hash of primary image
    fraud_flags     = Column(Text, nullable=True)     # JSON array: ["image_mismatch", "price_anomaly"]
    rejection_reason = Column(Text, nullable=True)
    
    # ── Semantic Recommendation fields ───────────────────────────────────────
    semantic_embedding = Column(Text, nullable=True)  # JSON array of float representing SentenceTransformer embedding
    
    # Relationships
    owner = relationship("User", back_populates="listings")
    messages = relationship("Message", back_populates="listing")
    favorites = relationship("Favorite", back_populates="listing")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
    listing = relationship("Listing", back_populates="messages")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    listing_id = Column(Integer, ForeignKey("listings.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="favorites")
    listing = relationship("Listing", back_populates="favorites")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_type = Column(String)  # 'support' or 'bug'
    subject = Column(String)
    description = Column(Text)
    status = Column(String, default="open")  # 'open', 'in_progress', 'closed'
    created_at = Column(DateTime, default=datetime.utcnow)
    attachment_url = Column(String, nullable=True)  # For screenshots

    # Relationships
    user = relationship("User", backref="tickets")

class UserActivity(Base):
    """Track user interactions for recommendations"""
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous users
    session_id = Column(String, index=True)  # For anonymous tracking
    activity_type = Column(String, index=True)  # 'search', 'view', 'click', 'favorite', 'message'
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    search_query = Column(String, nullable=True)
    category = Column(String, nullable=True)
    keywords = Column(Text, nullable=True)  # JSON array of extracted keywords
    semantic_embedding = Column(Text, nullable=True)  # JSON array of embedding vector
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_seconds = Column(Integer, nullable=True)  # Time spent on listing
    
class UserInterest(Base):
    """Aggregated user interests based on activity"""
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    categories = Column(Text)  # JSON object with category counts
    keywords = Column(Text)  # JSON object with keyword frequencies
    brands = Column(Text, nullable=True)  # JSON object with brand preferences
    semantic_embedding = Column(Text, nullable=True)  # Aggregated averaged embedding vector
    price_range_min = Column(Float, nullable=True)
    price_range_max = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_activities = Column(Integer, default=0)

class RecommendationHistory(Base):
    """Track recommendations shown to users"""
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    listing_id = Column(Integer, ForeignKey("listings.id"))
    recommendation_type = Column(String)  # 'interest_based', 'collaborative', 'trending', 'similar'
    score = Column(Float)
    shown_at = Column(DateTime, default=datetime.utcnow)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)

class MobilePhone(Base):
    """Category-specific details for mobile phones"""
    __tablename__ = "mobile_phones"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), unique=True)
    Title = Column(String)
    Brand = Column(String)
    Price = Column(Float)
    Condition = Column(String)
    Description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Laptop(Base):
    """Category-specific details for laptops"""
    __tablename__ = "laptops"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), unique=True)
    Title = Column(String)
    Price = Column(Float)
    Brand = Column(String)
    Model = Column(String, nullable=True)
    Condition = Column(String)
    Description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Furniture(Base):
    """Category-specific details for furniture"""
    __tablename__ = "furniture"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), unique=True)
    Title = Column(String)
    Price = Column(Float)
    Condition = Column(String)
    Type = Column(String)
    Material = Column(String, nullable=True)
    furniture_brand = Column(String, nullable=True)
    is_sliding_door = Column(Boolean, default=False)
    has_mattress = Column(Boolean, default=False)
    mattress_type = Column(String, nullable=True)
    Description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    link = Column(String, nullable=True)  # Optional link to redirect user
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="notifications")

class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"))
    blocked_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    reported_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # 'pending', 'resolved', 'ignored'
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
Base.metadata.create_all(bind=engine)
