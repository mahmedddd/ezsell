"""
Database models and connection setup
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./ezsell.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
    profile_picture = Column(String, nullable=True)

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
    token = Column(String, unique=True, index=True)
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
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)
    predicted_price = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    ar_model_url = Column(String, nullable=True)
    
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

# Create all tables
Base.metadata.create_all(bind=engine)
