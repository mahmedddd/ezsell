"""
Favorites/Saved Listings routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db, Favorite, User, Listing
from schemas.schemas import ListingResponse
from core.security import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/{listing_id}", status_code=status.HTTP_201_CREATED)
def add_to_favorites(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Add a listing to user's favorites"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="User not authenticated. Please login again.")
    
    # Check if listing exists
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check if already favorited
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.listing_id == listing_id
    ).first()
    
    if existing:
        return {"message": "Already in favorites", "is_favorited": True}
    
    # Create favorite
    favorite = Favorite(
        user_id=current_user.id,
        listing_id=listing_id
    )
    db.add(favorite)
    db.commit()
    
    return {"message": "Added to favorites", "is_favorited": True}

@router.delete("/{listing_id}", status_code=status.HTTP_200_OK)
def remove_from_favorites(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Remove a listing from user's favorites"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find and delete favorite
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.listing_id == listing_id
    ).first()
    
    if not favorite:
        return {"message": "Not in favorites", "is_favorited": False}
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "Removed from favorites", "is_favorited": False}

@router.get("/check/{listing_id}")
def check_favorite(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Check if a listing is in user's favorites"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        return {"is_favorited": False}
    
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.listing_id == listing_id
    ).first()
    
    return {"is_favorited": favorite is not None}

@router.get("/", response_model=List[ListingResponse])
def get_favorites(
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Get all favorite listings for current user"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all favorite listings
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    
    # Get the actual listings (only approved ones)
    listing_ids = [fav.listing_id for fav in favorites]
    listings = db.query(Listing).filter(
        Listing.id.in_(listing_ids),
        Listing.approval_status == "approved"
    ).all()
    
    return listings
