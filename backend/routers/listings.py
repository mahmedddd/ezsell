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
from schemas.schemas import ListingCreate, ListingUpdate, ListingResponse, ImageValidationResponse
from core.security import get_current_user, get_current_user_optional
from routers.users import get_user_by_username
from core.fraud_protection import FraudProtectionService
from services.cloud_storage import CloudStorageService
from core.config import settings

router = APIRouter()

# Create uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "listings"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return the file path or URL"""
    # Validate file extension
    file_ext = Path(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Try cloud upload first if configured
    try:
        cloud_url = await CloudStorageService.upload_file(upload_file)
        if cloud_url:
            return cloud_url
    except Exception as e:
        print(f"Cloud upload failed, falling back to local: {e}")

    # Fallback to local storage
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # Return relative path for URL
    return f"/uploads/listings/{unique_filename}"

@router.post("/validate-image", response_model=ImageValidationResponse)
async def validate_image(
    category: str = Form(...),
    image: UploadFile = File(...)
):
    """Real-time CLIP image validation for the frontend"""
    # Temporarily save the image to a temp file for CLIP
    temp_filename = f"temp_{uuid.uuid4()}_{image.filename}"
    temp_path = UPLOADS_DIR / temp_filename
    
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        is_match, confidence, best_label = await FraudProtectionService.validate_image_category(
            str(temp_path), category
        )
        
        return ImageValidationResponse(
            is_match=is_match,
            confidence=confidence,
            best_label=best_label
        )
    finally:
        # Clean up temp file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass

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
    is_sliding_door: bool = Form(False),
    has_mattress: bool = Form(False),
    mattress_type: Optional[str] = Form(None),
    furniture_brand: Optional[str] = Form(None),
    predicted_price: Optional[float] = Form(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product listing with image upload and price approval logic"""
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Initialize variables to avoid UnboundLocalError
    rejection_reason = None
    
    try:
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
        
        # ── Fraud Prevention & Approval Logic ────────────────────────────────────
        fraud_flags = []
        approval_status = "approved" # Default state
        
        # 1. Enforce Email Verification (Hard Rejection)
        if not FraudProtectionService.check_email_verified(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Your email is not verified. Please verify your email in settings to post ads."
            )

        # 2. Duplicate Ad Detection (Global)
        listing_hash = FraudProtectionService.generate_listing_hash(title, description, price)
        
        # We'll check for duplicates AFTER processing images to get the image hash
        duplicate_match = None

        # 3. Scam Keyword Filter
        scam_flags = FraudProtectionService.scan_for_scam_keywords(f"{title} {description}")
        if scam_flags:
            print(f"DEBUG: Scam keywords detected: {scam_flags}")
            approval_status = "pending"
            fraud_flags.append("scam_keywords_found")
        
        # 3b. Content Quality Check (Nonsense/Gibberish)
        is_nonsense_title, title_reason = FraudProtectionService.is_nonsense(title)
        is_nonsense_desc, desc_reason = FraudProtectionService.is_nonsense(description)
        
        if is_nonsense_title or is_nonsense_desc:
            print(f"DEBUG: Nonsense detected. Title: {title_reason}, Desc: {desc_reason}")
            approval_status = "pending"
            fraud_flags.append("quality_issue")
            # Log specific reason for internal tracking if needed
            rejection_reason = f"Quality issue: {title_reason if is_nonsense_title else desc_reason}"
        
        # Handle multiple image uploads (max 5)
        image_url = None
        additional_images_list = []
        
        if images:
            # Limit to 5 images
            images_to_process = images[:5]
            
            # First image becomes the main image_url
            if len(images_to_process) > 0 and images_to_process[0].filename:
                image_url = await save_upload_file(images_to_process[0])
            
            # Remaining images go to additional_images
            for img in images_to_process[1:]:
                if img.filename:
                    img_url = await save_upload_file(img)
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

        # 4. Price Anomaly Check (against predicted price)
        if predicted_price:
            is_anomaly, reason = FraudProtectionService.check_price_anomaly(price, predicted_price)
            if is_anomaly:
                print(f"DEBUG: Price anomaly detected: {reason}")
                approval_status = "pending"
                fraud_flags.append(f"price_{reason}")

        # 5. Image Hashing (dHash) for all images
        image_hashes = []
        if image_url:
            abs_main_path = Path(__file__).parent.parent / image_url.lstrip('/')
            main_hash = FraudProtectionService.calculate_image_hash(str(abs_main_path))
            image_hash = main_hash # Stoing main hash for the DB record
            if main_hash: image_hashes.append(main_hash)
            
            # Check additional images too
            for img_path in additional_images_list:
                abs_extra_path = Path(__file__).parent.parent / img_path.lstrip('/')
                extra_h = FraudProtectionService.calculate_image_hash(str(abs_extra_path))
                if extra_h: image_hashes.append(extra_h)

            # Perform Global Duplicate Check (Content + ALL Images)
            duplicate_match = FraudProtectionService.is_duplicate(db, listing_hash, image_hashes)
            if duplicate_match:
                print(f"DEBUG: Duplicate detected. Match ID: {duplicate_match.id}")
                approval_status = "pending"
                if "duplicate_detected" not in fraud_flags:
                    fraud_flags.append("duplicate_detected")
                
                # Check if it was specifically an image match
                is_img_match = False
                for h in image_hashes:
                    if h == duplicate_match.image_hash:
                        is_img_match = True
                        break
                if is_img_match and "duplicate_image" not in fraud_flags:
                    fraud_flags.append("duplicate_image")

            # 6. Category Validation (CLIP AI) - Check ALL uploaded images
            all_image_paths = []
            if image_url: all_image_paths.append(image_url)
            all_image_paths.extend(additional_images_list)
            
            for img_path in all_image_paths:
                abs_img_path = Path(__file__).parent.parent / img_path.lstrip('/')
                is_match, confidence, best_label = await FraudProtectionService.validate_image_category(
                    str(abs_img_path), category
                )
                
                if not is_match:
                    # Delete ALL uploaded images to save space
                    for to_delete in all_image_paths:
                        try: (Path(__file__).parent.parent / to_delete.lstrip('/')).unlink()
                        except: pass
                        
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Image-Category Mismatch! One of your images was detected as '{best_label}', which doesn't match the '{category}' category. Please upload correct photos."
                    )

        if fraud_flags:
            approval_status = "pending" if approval_status != "rejected" else "rejected"
        
        # Create base listing
        db_listing = Listing(
            title=title,
            description=description,
            price=price,
            category=category,
            brand=brand,
            condition=condition,
            location=location,
            furniture_type=furniture_type if category == "furniture" else None,
            material=material if category == "furniture" else None,
            furniture_subtype=furniture_subtype if category == "furniture" else None,
            furniture_brand=furniture_brand if category == "furniture" else None,
            is_sliding_door=is_sliding_door if category == "furniture" else False,
            has_mattress=has_mattress if category == "furniture" else False,
            mattress_type=mattress_type if category == "furniture" else None,
            images=images_json,
            owner_id=user.id,
            approval_status=approval_status,
            predicted_price=predicted_price,
            listing_hash=listing_hash,
            image_hash=image_hash,
            fraud_flags=json.dumps(fraud_flags) if fraud_flags else None
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
                furniture_brand=furniture_brand,
                is_sliding_door=is_sliding_door,
                has_mattress=has_mattress,
                mattress_type=mattress_type,
                Description=description
            )
            db.add(furniture_details)
        
        db.commit()
        db.refresh(db_listing)
        return db_listing
    except HTTPException:
        raise
    except Exception:
        import traceback
        with open("direct_listings_error.log", "a") as f:
            f.write(f"\n--- {datetime.utcnow()} ---\n")
            f.write(traceback.format_exc())
            f.write("\n")
        raise

@router.get("/listings", response_model=List[ListingResponse])
def get_listings(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    condition: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all listings with optional filters (only approved listings)"""
    # Calculate expiration date (30 days ago)
    from datetime import timedelta
    expiry_limit = datetime.utcnow() - timedelta(days=30)

    query = db.query(Listing).filter(
        Listing.is_sold == False,
        Listing.approval_status == "approved",
        Listing.is_active == True,
        Listing.created_at >= expiry_limit
    )
    
    if category:
        query = query.filter(Listing.category == category)
    if condition:
        query = query.filter(Listing.condition == condition)
    if min_price:
        query = query.filter(Listing.price >= min_price)
    if max_price:
        query = query.filter(Listing.price <= max_price)
    if owner_id:
        query = query.filter(Listing.owner_id == owner_id)
    if search:
        from sqlalchemy import or_

        # English stopwords — skip these so they don't match irrelevant listings
        STOPWORDS = {
            'a', 'an', 'the', 'and', 'or', 'for', 'with', 'in', 'on', 'at',
            'to', 'of', 'is', 'it', 'its', 'be', 'as', 'by', 'are', 'was',
            'my', 'i', 'me', 'we', 'you', 'he', 'she', 'they', 'this', 'that',
        }

        def _stem(word: str) -> str:
            """Strip common English plural suffixes for singular/plural matching."""
            w = word.lower()
            if w.endswith('ing') and len(w) > 5:  # running→run, selling→sell
                return w[:-3]
            if w.endswith('ies') and len(w) > 4:  # categories→categor (matches category)
                return w[:-3] + 'y'
            if w.endswith('ers') and len(w) > 4:  # sellers→seller
                return w[:-1]
            if w.endswith('es') and len(w) > 4:   # couches→couch
                return w[:-2]
            if w.endswith('s') and len(w) > 3:    # beds→bed, phones→phone
                return w[:-1]
            return w

        # Tokenise: split on whitespace/punctuation, drop short/stopwords
        import re
        raw_words = re.split(r'[\s\-_/,]+', search.strip())
        # Allow short numeric tokens (e.g. model numbers '6', '7s') even if len < 2
        words = [w.lower() for w in raw_words if (len(w) >= 2 or w.isdigit()) and w.lower() not in STOPWORDS]

        if not words:
            words = [search.strip().lower()]  # fallback: use the raw query

        for word in words:
            stemmed = _stem(word)
            # Build text variants: original + stemmed (deduped)
            variants = list({word, stemmed})

            # Match against ALL listing text fields — any field can satisfy the keyword
            word_filters = []
            for v in variants:
                pat = f"%{v}%"
                word_filters.extend([
                    Listing.title.ilike(pat),
                    Listing.description.ilike(pat),
                    Listing.brand.ilike(pat),
                    Listing.category.ilike(pat),
                    Listing.condition.ilike(pat),
                    Listing.furniture_type.ilike(pat),
                    Listing.material.ilike(pat),
                    Listing.location.ilike(pat),
                ])

            query = query.filter(or_(*word_filters))

    
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
    from sqlalchemy.orm import joinedload
    listing = db.query(Listing).options(joinedload(Listing.owner)).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check if listing is approved or if user is the owner
    user = None
    if current_user:
        # Import here to avoid circular imports if any
        from routers.users import get_user_by_username
        user = get_user_by_username(db, username=current_user.username)
    
    # Allow owner to view their own listing regardless of status
    if listing.approval_status != "approved" and (not user or listing.owner_id != user.id):
        raise HTTPException(
            status_code=404, 
            detail="Listing not found or not yet approved"
        )
    
    # Increment view count only for approved listings, and only for non-owners
    is_owner = user and listing.owner_id == user.id
    if listing.approval_status == "approved" and not is_owner:
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

@router.post("/listings/{listing_id}/track-call")
async def track_call(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Notify seller that buyer viewed their phone number and initialize chat"""
    from models.database import Message
    
    # Get buyer
    buyer = db.query(User).filter(User.username == current_user_token.username).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
        
    # Get listing and seller
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    seller = listing.owner
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
        
    if buyer.id == seller.id:
        return {"phone": seller.phone, "message": "Owner viewing own listing"}

    # Create automated message
    message_content = f"Hello! I just viewed your phone number regarding your listing '{listing.title}'. I might be calling you soon!"
    
    # Check if this exact automated message was already sent recently to avoid spam
    existing_msg = db.query(Message).filter(
        Message.sender_id == buyer.id,
        Message.receiver_id == seller.id,
        Message.listing_id == listing_id,
        Message.content == message_content
    ).first()
    
    if not existing_msg:
        db_message = Message(
            content=message_content,
            sender_id=buyer.id,
            receiver_id=seller.id,
            listing_id=listing_id
        )
        db.add(db_message)
        db.commit()

    return {"phone": seller.phone, "message": "Notification sent to seller"}

@router.get("/my-listings")
def get_my_listings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all listings created by the current user"""
    from routers.users import get_user_by_username
    user = get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    listings = db.query(Listing).filter(Listing.owner_id == user.id).order_by(Listing.created_at.desc()).all()
    # Explicitly build response dicts to ensure is_active is included
    result = []
    for l in listings:
        import json as _json
        result.append({
            "id": l.id,
            "title": l.title,
            "description": l.description,
            "price": l.price,
            "category": l.category,
            "condition": l.condition,
            "location": l.location,
            "images": l.images,
            "brand": l.brand,
            "furniture_type": l.furniture_type,
            "material": l.material,
            "furniture_subtype": l.furniture_subtype,
            "furniture_brand": l.furniture_brand,
            "is_sliding_door": bool(l.is_sliding_door) if l.is_sliding_door is not None else False,
            "has_mattress": bool(l.has_mattress) if l.has_mattress is not None else False,
            "mattress_type": l.mattress_type,
            "owner_id": l.owner_id,
            "views": l.views or 0,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "updated_at": l.updated_at.isoformat() if l.updated_at else None,
            "is_active": bool(l.is_active) if l.is_active is not None else True,
            "is_sold": bool(l.is_sold) if l.is_sold is not None else False,
            "approval_status": l.approval_status or "approved",
            "predicted_price": l.predicted_price,
            "fraud_flags": l.fraud_flags,
            "rejection_reason": l.rejection_reason,
            "owner": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
            } if user else None,
        })
    return result


@router.patch("/listings/{listing_id}/status")
def update_listing_status(
    listing_id: int,
    updates: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle is_active (hide/unhide) or is_sold for a listing"""
    from routers.users import get_user_by_username
    user = get_user_by_username(db, username=current_user.username)
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.owner_id == user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if "is_active" in updates:
        listing.is_active = bool(updates["is_active"])
    if "is_sold" in updates:
        listing.is_sold = bool(updates["is_sold"])
        if updates["is_sold"]:
            listing.is_active = False  # sold items are automatically hidden
    db.commit()
    db.refresh(listing)
    return {"message": "Status updated", "is_active": bool(listing.is_active), "is_sold": bool(listing.is_sold)}

@router.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload an image and return the URL"""
    image_url = await save_upload_file(image)
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
