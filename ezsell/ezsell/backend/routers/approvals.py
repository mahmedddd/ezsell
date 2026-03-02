# Admin approval and notification endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from models.database import get_db, Listing, User, Message
from schemas.schemas import ListingResponse
from core.security import get_current_user
from routers.users import get_user_by_username

router = APIRouter()

def get_admin_user(db: Session, current_user) -> User:
    """Helper function to verify admin user"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/admin/pending-listings", response_model=List[ListingResponse])
def get_pending_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all listings pending approval (admin only)"""
    admin = get_admin_user(db, current_user)
    
    pending_listings = db.query(Listing).filter(
        Listing.approval_status == "pending"
    ).order_by(Listing.created_at.desc()).all()
    
    return pending_listings

@router.post("/admin/approve-listing/{listing_id}")
def approve_listing(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a pending listing (admin only)"""
    admin = get_admin_user(db, current_user)
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.approval_status != "pending":
        raise HTTPException(status_code=400, detail="Listing is not pending approval")
    
    # Update listing status
    listing.approval_status = "approved"
    listing.reviewed_at = datetime.utcnow()
    listing.reviewed_by = admin.id
    
    # Send notification message to owner
    notification = Message(
        sender_id=admin.id,
        receiver_id=listing.owner_id,
        listing_id=listing.id,
        content=f"✅ Great news! Your listing '{listing.title}' has been approved and is now live on EZSELL. Buyers can now see and purchase your item.",
        is_read=False
    )
    db.add(notification)
    
    db.commit()
    db.refresh(listing)
    
    return {
        "message": "Listing approved successfully",
        "listing_id": listing.id,
        "title": listing.title,
        "status": listing.approval_status
    }

@router.post("/admin/reject-listing/{listing_id}")
def reject_listing(
    listing_id: int,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a pending listing (admin only)"""
    admin = get_admin_user(db, current_user)
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.approval_status != "pending":
        raise HTTPException(status_code=400, detail="Listing is not pending approval")
    
    # Update listing status
    listing.approval_status = "rejected"
    listing.rejection_reason = reason
    listing.reviewed_at = datetime.utcnow()
    listing.reviewed_by = admin.id
    
    # Send notification message to owner
    notification = Message(
        sender_id=admin.id,
        receiver_id=listing.owner_id,
        listing_id=listing.id,
        content=f"❌ Your listing '{listing.title}' has been rejected. Reason: {reason}. Please review the pricing or contact support for more information.",
        is_read=False
    )
    db.add(notification)
    
    db.commit()
    db.refresh(listing)
    
    return {
        "message": "Listing rejected",
        "listing_id": listing.id,
        "title": listing.title,
        "status": listing.approval_status,
        "reason": reason
    }

@router.get("/my-pending-listings", response_model=List[ListingResponse])
def get_my_pending_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's pending listings"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    pending_listings = db.query(Listing).filter(
        Listing.owner_id == user.id,
        Listing.approval_status == "pending"
    ).order_by(Listing.created_at.desc()).all()
    
    result = []
    for listing in pending_listings:
        price_diff = None
        if listing.predicted_price:
            price_diff = listing.price - listing.predicted_price
        
        result.append({
            "id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "predicted_price": listing.predicted_price,
            "price_difference": price_diff,
            "category": listing.category,
            "condition": listing.condition,
            "image_url": listing.image_url,
            "created_at": listing.created_at,
            "approval_status": listing.approval_status
        })
    
    return result

@router.get("/my-rejected-listings", response_model=List[ListingResponse])
def get_my_rejected_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's rejected listings"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    rejected_listings = db.query(Listing).filter(
        Listing.owner_id == user.id,
        Listing.approval_status == "rejected"
    ).order_by(Listing.created_at.desc()).all()
    
    result = []
    for listing in rejected_listings:
        result.append({
            "id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "predicted_price": listing.predicted_price,
            "category": listing.category,
            "condition": listing.condition,
            "image_url": listing.image_url,
            "rejection_reason": listing.rejection_reason,
            "reviewed_at": listing.reviewed_at,
            "created_at": listing.created_at
        })
    
    return result
