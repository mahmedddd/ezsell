# Product listings endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from pathlib import Path
import uuid
from datetime import datetime
import json
import re


# ─── Generic furniture_subtype inference ──────────────────────────────────────
def _infer_furniture_subtype(furniture_type: str, text: str) -> Optional[str]:
    """
    Infer furniture_subtype from listing title + description when the user
    hasn't explicitly provided one.  Mirrors the frontend resolveSmartDimensions
    / parseDoorCount rules so both sides stay in sync.
    """
    t = text.lower()
    ft = (furniture_type or '').lower().strip()

    if ft == 'wardrobe':
        if re.search(r'6[\s-]*door|six[\s-]*door', t):    return '6_door'
        if re.search(r'5[\s-]*door|five[\s-]*door', t):    return '5_door'
        if re.search(r'4[\s-]*door|four[\s-]*door', t):    return '4_door'
        if re.search(r'3[\s-]*door|three[\s-]*door', t):   return '3_door'
        if re.search(r'2[\s-]*door|two[\s-]*door', t):     return '2_door'
        if re.search(r'sliding', t):                        return 'sliding'
        if re.search(r'walk[\s-]*in', t):                   return 'walk_in'
        return '2_door'

    if ft in ('sofa', 'couch'):
        if re.search(r'7[\s-]*seater|seven[\s-]*seater', t): return '7_seater'
        if re.search(r'6[\s-]*seater|six[\s-]*seater', t):   return '6_seater'
        if re.search(r'5[\s-]*seater|five[\s-]*seater', t):  return '5_seater'
        if re.search(r'4[\s-]*seater|four[\s-]*seater', t):  return '4_seater'
        if re.search(r'3[\s-]*seater|three[\s-]*seater', t): return '3_seater'
        if re.search(r'2[\s-]*seater|two[\s-]*seater|loveseat', t): return '2_seater'
        if re.search(r'1[\s-]*seater|single[\s-]*seater', t): return '1_seater'
        if re.search(r'l[\s-]*shaped|sectional', t):          return 'l_shaped'
        if re.search(r'sofa.{0,10}bed|sofa.{0,10}cum|cum.{0,10}bed', t): return 'sofa_cum_bed'
        if re.search(r'recliner', t):                          return 'recliner'
        return '3_seater'

    if ft == 'bed':
        if re.search(r'king[\s-]*size|king[\s-]*bed|\bking\b', t):     return 'king'
        if re.search(r'queen[\s-]*size|queen[\s-]*bed|\bqueen\b', t):  return 'queen'
        if re.search(r'double[\s-]*bed|full[\s-]*size|\bdouble\b', t): return 'double'
        if re.search(r'bunk[\s-]*bed|\bbunk\b', t):                    return 'bunk'
        if re.search(r'single[\s-]*bed|twin[\s-]*bed|\bsingle\b|\btwin\b', t): return 'single'
        return 'double'

    if ft in ('table', 'dining_table'):
        if re.search(r'10[\s-]*seater|ten[\s-]*person', t):  return 'dining_8'
        if re.search(r'8[\s-]*seater|eight[\s-]*person', t): return 'dining_8'
        if re.search(r'6[\s-]*seater|six[\s-]*person', t):   return 'dining_6'
        if re.search(r'4[\s-]*seater|four[\s-]*person', t):  return 'dining_4'
        if re.search(r'2[\s-]*seater|two[\s-]*person', t):   return 'dining_4'
        if re.search(r'coffee', t):                           return 'coffee'
        if re.search(r'side[\s-]*table|end[\s-]*table', t):  return 'side'
        if re.search(r'console', t):                          return 'console'
        if re.search(r'study|writing', t):                    return 'study'
        return 'dining_4'

    if ft == 'coffee_table':
        return 'coffee'

    if ft in ('chair', 'armchair'):
        if re.search(r'gaming[\s-]*chair', t):                return 'gaming'
        if re.search(r'office[\s-]*chair|revolving|executive[\s-]*chair', t): return 'office'
        if re.search(r'rocking[\s-]*chair|\brocking\b', t):   return 'rocking'
        if re.search(r'dining[\s-]*chair|\bdining\b', t):     return 'dining'
        if re.search(r'accent', t):                            return 'accent'
        if re.search(r'bean[\s-]*bag', t):                     return 'bean_bag'
        return 'dining'

    if ft == 'office_chair':
        return 'office'

    if ft == 'dining_chair':
        return 'dining'

    if ft == 'desk':
        if re.search(r'l[\s-]*shaped', t):                    return 'l_shaped'
        if re.search(r'standing[\s-]*desk|stand[\s-]*up', t): return 'standing'
        if re.search(r'executive', t):                         return 'executive'
        if re.search(r'computer[\s-]*desk|pc[\s-]*desk', t):  return 'computer'
        if re.search(r'writing[\s-]*desk|\bwriting\b', t):    return 'writing'
        if re.search(r'study', t):                             return 'writing'
        return 'computer'

    if ft == 'cabinet':
        if re.search(r'kitchen[\s-]*cabinet', t):             return 'kitchen'
        if re.search(r'bathroom|washroom', t):                 return 'bathroom'
        if re.search(r'display[\s-]*cabinet|showcase', t):    return 'display'
        if re.search(r'filing[\s-]*cabinet|file[\s-]*cabinet', t): return 'filing'
        return 'storage'

    if ft in ('bookshelf', 'shelf'):
        if re.search(r'wall[\s-]*shelf|floating[\s-]*shelf', t): return 'wall_shelf'
        if re.search(r'corner[\s-]*shelf', t):                   return 'corner'
        if re.search(r'shoe[\s-]*rack|shoes?\s+rack', t):        return 'shoe_rack'
        return 'bookshelf'

    if ft in ('dresser', 'dressing_table'):
        if re.search(r'vanity', t):                return 'vanity'
        if re.search(r'mirror', t):                return 'with_mirror'
        if re.search(r'storage|drawer', t):        return 'with_storage'
        return 'simple'

    if ft == 'ottoman':
        if re.search(r'round|circular|pouf', t):  return 'round'
        if re.search(r'storage', t):               return 'storage'
        return 'rectangular'

    return None  # Unknown type — leave NULL

from models.database import get_db, Listing, User, MobilePhone, Laptop, Furniture
from schemas.schemas import ListingCreate, ListingUpdate, ListingResponse
from core.security import get_current_user, get_current_user_optional
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
    furniture_subtype: Optional[str] = Form(None),
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
    
    # Auto-infer furniture_subtype from title+description when not provided
    if category == 'furniture' and furniture_type and not furniture_subtype:
        combined_text = f"{title} {description or ''}"
        furniture_subtype = _infer_furniture_subtype(furniture_type, combined_text)

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
        furniture_subtype=furniture_subtype,
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
    current_user = Depends(get_current_user_optional)
):
    """Get a specific listing by ID (approved listings are public; pending/rejected require ownership)"""
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
