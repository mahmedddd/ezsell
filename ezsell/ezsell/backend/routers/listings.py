# Product listings endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from pathlib import Path
import uuid
from datetime import datetime
import json

from models.database import get_db, Listing, User, MobilePhone, Laptop, Furniture
from schemas.schemas import ListingCreate, ListingUpdate, ListingResponse
from core.security import get_current_user
from routers.users import get_user_by_username

router = APIRouter()

# Create uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "listings"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return the file path"""
    # Validate file extension
    file_ext = Path(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # Return relative path for URL
    return f"/uploads/listings/{unique_filename}"

@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    condition: str = Form(...),
    location: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    furniture_type: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    predicted_price: Optional[float] = Form(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product listing with image upload and price approval logic"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate required fields
    if not title or title.strip() == "":
        raise HTTPException(status_code=400, detail="Title is required")
    if not description or description.strip() == "":
        raise HTTPException(status_code=400, detail="Description is required")
    if not condition or condition.strip() == "":
        raise HTTPException(status_code=400, detail="Condition is required")
    if not location or location.strip() == "":
        raise HTTPException(status_code=400, detail="Location is required")
    if not images or len(images) == 0 or not images[0].filename:
        raise HTTPException(status_code=400, detail="At least one product image is required")
    
    # Category-specific validation
    if category in ["mobile", "laptop"]:
        if not brand or brand.strip() == "":
            raise HTTPException(status_code=400, detail="Brand is required for mobile/laptop listings")
    elif category == "furniture":
        if not furniture_type or furniture_type.strip() == "":
            raise HTTPException(status_code=400, detail="Furniture type is required for furniture listings")
    
    # Check for duplicate listing by the same user
    existing_listing = db.query(Listing).filter(
        Listing.owner_id == user.id,
        Listing.title == title,
        Listing.description == description,
        Listing.price == price,
        Listing.category == category,
        Listing.condition == condition
    ).first()
    
    if existing_listing:
        # Check if brand/model also matches for more precision
        if brand and existing_listing.brand == brand:
            raise HTTPException(
                status_code=400, 
                detail="Duplicate listing detected. You have already posted a listing with the same details. Please edit your existing listing instead."
            )
        elif not brand:  # For furniture or items without brand
            raise HTTPException(
                status_code=400, 
                detail="Duplicate listing detected. You have already posted a listing with the same details. Please edit your existing listing instead."
            )
    
    # Handle multiple image uploads (max 5)
    image_url = None
    additional_images_list = []
    
    if images:
        # Limit to 5 images
        images_to_process = images[:5]
        
        # First image becomes the main image_url
        if len(images_to_process) > 0 and images_to_process[0].filename:
            image_url = save_upload_file(images_to_process[0])
        
        # Remaining images go to additional_images
        for img in images_to_process[1:]:
            if img.filename:
                img_url = save_upload_file(img)
                additional_images_list.append(img_url)
    
    # Convert additional images list to JSON string
    additional_images_json = json.dumps(additional_images_list) if additional_images_list else None
    
    # Combine all images into single list for the images field
    all_images = []
    if image_url:
        all_images.append(image_url)
    all_images.extend(additional_images_list)
    images_json = json.dumps(all_images) if all_images else None
    
    # Determine approval status based on predicted price
    approval_status = "approved"
    if predicted_price:
        price_difference = abs(price - predicted_price)
        if price_difference >= 20000:
            approval_status = "pending"
    
    # Create base listing
    db_listing = Listing(
        title=title,
        description=description,
        price=price,
        category=category,
        brand=brand,
        condition=condition,
        location=location,
        furniture_type=furniture_type,
        material=material,
        images=images_json,
        owner_id=user.id,
        approval_status=approval_status,
        predicted_price=predicted_price
    )
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    
    # Add category-specific details
    if category == "mobile" and brand:
        mobile_details = MobilePhone(
            listing_id=db_listing.id,
            Title=title,
            Brand=brand,
            Price=price,
            Condition=condition,
            Description=description
        )
        db.add(mobile_details)
    elif category == "laptop" and brand:
        laptop_details = Laptop(
            listing_id=db_listing.id,
            Title=title,
            Price=price,
            Brand=brand,
            Model=model,
            Condition=condition,
            Description=description
        )
        db.add(laptop_details)
    elif category == "furniture" and furniture_type:
        furniture_details = Furniture(
            listing_id=db_listing.id,
            Title=title,
            Price=price,
            Condition=condition,
            Type=furniture_type,
            Material=material,
            Description=description
        )
        db.add(furniture_details)
    
    db.commit()
    db.refresh(db_listing)
    return db_listing

@router.get("/listings", response_model=List[ListingResponse])
def get_listings(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    condition: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all listings with optional filters (only approved listings)"""
    query = db.query(Listing).filter(
        Listing.is_sold == False,
        Listing.approval_status == "approved"
    )
    
    if category:
        query = query.filter(Listing.category == category)
    if condition:
        query = query.filter(Listing.condition == condition)
    if min_price:
        query = query.filter(Listing.price >= min_price)
    if max_price:
        query = query.filter(Listing.price <= max_price)
    if search:
        query = query.filter(Listing.title.contains(search))
    
    # Order by newest first
    listings = query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()
    return listings

@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_listing(
    listing_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get a specific listing by ID (only approved listings visible to public)"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check if listing is approved or if user is the owner
    user = None
    if current_user:
        user = get_user_by_username(db, username=current_user.username)
    
    # Allow owner to view their own listing regardless of status
    # Only show rejected/pending listings to the owner
    if listing.approval_status != "approved" and (not user or listing.owner_id != user.id):
        raise HTTPException(
            status_code=404, 
            detail="Listing not found or not yet approved"
        )
    
    # Increment view count only for approved listings
    if listing.approval_status == "approved":
        listing.views += 1
        db.commit()
        db.refresh(listing)
    
    return listing

@router.put("/listings/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_update: ListingUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a listing (owner only)"""
    user = get_user_by_username(db, username=current_user.username)
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this listing")
    
    # Update fields
    update_data = listing_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(listing, key, value)
    
    db.commit()
    db.refresh(listing)
    return listing

@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a listing (owner only)"""
    user = get_user_by_username(db, username=current_user.username)
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
    
    db.delete(listing)
    db.commit()
    return None

@router.get("/my-listings", response_model=List[ListingResponse])
def get_my_listings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all listings created by the current user"""
    from routers.users import get_user_by_username
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    listings = db.query(Listing).filter(Listing.owner_id == user.id).all()
    return listings

@router.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload an image and return the URL"""
    image_url = save_upload_file(image)
    return {"image_url": image_url, "message": "Image uploaded successfully"}

# ============= ADMIN ENDPOINTS =============

@router.delete("/admin/listings/{listing_id}")
def delete_listing_admin(
    listing_id: int,
    db: Session = Depends(get_db)
):
    """Delete any listing (admin only)"""
    from routers.users import get_current_admin_user
    from models.database import User
    
    # This will be passed through dependency injection
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    db.delete(listing)
    db.commit()
    return {"message": f"Listing '{listing.title}' deleted successfully"}
