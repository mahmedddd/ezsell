"""
AR Assets Router
────────────────
Provides endpoints for managing 3-D AR model metadata and file uploads
for furniture listings.

Routes:
  GET  /products/{id}/assets           – public: fetch AR asset metadata
  PUT  /products/{id}/assets           – admin/owner: update metadata fields
  POST /products/{id}/assets/upload-glb – admin/owner: upload a .glb file
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from typing import Optional
import json
import uuid
import shutil

from models.database import get_db, Listing
from core.security import get_current_user
from routers.users import get_user_by_username
import os


# 3D Assets only (Manual/Procedural)
_IMAGE_TO_3D_AVAILABLE = False
print("✅ [AR_ASSETS] AR Assets router initialized.")

router = APIRouter()

# Directory where uploaded GLB/USDZ files are stored
AR_MODELS_DIR = Path(__file__).parent.parent / "uploads" / "ar_models"
AR_MODELS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MODEL_EXTENSIONS = {".glb", ".usdz"}
MAX_MODEL_SIZE_MB = 50


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_ar_columns(db: Session):
    """Silently add new AR columns if this is an older SQLite DB (migration)."""
    cols_to_add = [
        ("model_glb_url",  "TEXT"),
        ("model_usdz_url", "TEXT"),
        ("dimensions_cm",  "TEXT"),
        ("polygon_count",  "INTEGER"),
    ]
    existing = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(listings)")).fetchall()
    }
    for col, col_type in cols_to_add:
        if col not in existing:
            db.execute(text(f"ALTER TABLE listings ADD COLUMN {col} {col_type}"))
    db.commit()


def _get_listing_or_404(listing_id: int, db: Session) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


def _serialize_assets(listing: Listing) -> dict:
    dims = None
    if listing.dimensions_cm:
        try:
            dims = json.loads(listing.dimensions_cm)
        except Exception:
            pass

    return {
        "listing_id":    listing.id,
        "model_glb_url":  listing.model_glb_url,
        "model_usdz_url": listing.model_usdz_url,
        "dimensions_cm":  dims,
        "polygon_count":  listing.polygon_count,
        "furniture_type": listing.furniture_type,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/products/{listing_id}/assets")
def get_ar_assets(listing_id: int, db: Session = Depends(get_db)):
    """
    Public endpoint.
    Returns AR model URLs + dimensions for a furniture listing.
    Returns null fields gracefully when no 3-D model has been uploaded yet –
    the frontend will generate a procedural GLB instead.
    """
    _ensure_ar_columns(db)
    listing = _get_listing_or_404(listing_id, db)

    if listing.category.lower() != "furniture":
        raise HTTPException(
            status_code=400,
            detail="AR assets are only available for furniture listings"
        )

    return _serialize_assets(listing)


@router.put("/products/{listing_id}/assets")
def update_ar_assets(
    listing_id: int,
    model_glb_url:  Optional[str] = None,
    model_usdz_url: Optional[str] = None,
    dimensions_cm:  Optional[str] = None,   # JSON string: {"l":int,"w":int,"h":int}
    polygon_count:  Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Owner or admin endpoint.
    Updates AR metadata fields for a listing.
    `dimensions_cm` must be a JSON string like '{"l":200,"w":90,"h":85}'.
    """
    _ensure_ar_columns(db)
    listing = _get_listing_or_404(listing_id, db)
    user = get_user_by_username(db, current_user.username)

    if not user:
        raise HTTPException(status_code=403, detail="User not found")
    if listing.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    # Validate dimensions JSON if provided
    if dimensions_cm is not None:
        try:
            parsed = json.loads(dimensions_cm)
            required = {"l", "w", "h"}
            if not required.issubset(parsed.keys()):
                raise ValueError
            listing.dimensions_cm = json.dumps(
                {k: int(parsed[k]) for k in required}
            )
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=400,
                detail="dimensions_cm must be JSON with keys l, w, h (integers in cm)"
            )

    if model_glb_url  is not None: listing.model_glb_url  = model_glb_url
    if model_usdz_url is not None: listing.model_usdz_url = model_usdz_url
    if polygon_count  is not None: listing.polygon_count  = polygon_count

    db.commit()
    db.refresh(listing)
    return _serialize_assets(listing)


@router.post("/products/{listing_id}/assets/upload-glb", status_code=status.HTTP_201_CREATED)
async def upload_glb(
    listing_id: int,
    glb_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Owner or admin endpoint.
    Accepts a .glb or .usdz file, saves it to disk, and updates the listing's
    model URL. The file is served via the /uploads static mount.
    """
    _ensure_ar_columns(db)
    listing = _get_listing_or_404(listing_id, db)
    user = get_user_by_username(db, current_user.username)

    if not user:
        raise HTTPException(status_code=403, detail="User not found")
    if listing.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    # Validate extension
    suffix = Path(glb_file.filename or "").suffix.lower()
    if suffix not in ALLOWED_MODEL_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_MODEL_EXTENSIONS)}"
        )

    # Validate size
    content = await glb_file.read()
    if len(content) > MAX_MODEL_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {MAX_MODEL_SIZE_MB} MB"
        )

    # Save file
    unique_name = f"{uuid.uuid4()}{suffix}"
    dest_path   = AR_MODELS_DIR / unique_name
    with dest_path.open("wb") as f:
        f.write(content)

    relative_url = f"/uploads/ar_models/{unique_name}"

    # Update listing
    if suffix == ".glb":
        listing.model_glb_url = relative_url
    elif suffix == ".usdz":
        listing.model_usdz_url = relative_url

    db.commit()
    db.refresh(listing)

    return {
        "message": "3D model uploaded successfully",
        "url": relative_url,
        "format": suffix.lstrip("."),
        **_serialize_assets(listing),
    }

# ─── AI 3D Generation (Tripo AI) ──────────────────────────────────────────────

@router.post("/products/{listing_id}/assets/generate-3d")
async def generate_3d_ai(
    listing_id: int,
    image_url: Optional[str] = Query(None),
    all_images: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Experimental endpoint: Generate a 3-D mesh from product images via Tripo AI.
    If all_images=True and the listing has multiple images, uses multiview_to_model.
    """
    from services.image_to_3d import (
        start_image_to_3d_task, 
        start_multiview_to_3d_task,
        upload_image_to_tripo
    )
    
    listing = _get_listing_or_404(listing_id, db)
    user = get_user_by_username(db, current_user.username)
    if not user or (listing.owner_id != user.id and not user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorised")

    try:
        # Helper to get absolute path from relative DB path
        def get_abs_path(rel_p: str):
            if not rel_p: return None
            # If it's already a full disk path or URL, ignore
            if rel_p.startswith("/") and not rel_p.startswith("//"):
                # Check /uploads/ vs something else
                if rel_p.startswith("/uploads/"):
                    return str(Path(__file__).parent.parent / rel_p.lstrip("/"))
            return None

        if all_images:
            img_list = json.loads(listing.images) if listing.images else []
            if len(img_list) > 1:
                # Upload all to Tripo and get tokens
                tokens = []
                for img in img_list:
                    abs_p = get_abs_path(img)
                    if abs_p and os.path.exists(abs_p):
                        token = await upload_image_to_tripo(abs_p)
                        tokens.append(token)
                
                if not tokens: raise ValueError("No valid local images found to upload")
                task_id = await start_multiview_to_3d_task(file_tokens=tokens)
            else:
                target = image_url or (img_list[0] if img_list else None)
                if not target: raise ValueError("No image found")
                
                abs_p = get_abs_path(target)
                if abs_p and os.path.exists(abs_p):
                    token = await upload_image_to_tripo(abs_p)
                    task_id = await start_image_to_3d_task(file_token=token)
                else:
                    # Fallback to URL if it's already a full URL or not local
                    full_url = target if target.startswith("http") else f"http://localhost:8000{target}"
                    task_id = await start_image_to_3d_task(image_url=full_url)
        else:
            if not image_url: raise ValueError("image_url required for single-image gen")
            
            abs_p = get_abs_path(image_url)
            if abs_p and os.path.exists(abs_p):
                token = await upload_image_to_tripo(abs_p)
                task_id = await start_image_to_3d_task(file_token=token)
            else:
                full_url = image_url if image_url.startswith("http") else f"http://localhost:8000{image_url}"
                task_id = await start_image_to_3d_task(image_url=full_url)
            
        return {"task_id": task_id, "status": "queued"}
    except Exception as e:
        import traceback
        print(f"❌ [AR_ASSETS] AI Gen Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/products/{listing_id}/assets/generate-3d/{task_id}")
async def poll_3d_ai_status(
    listing_id: int,
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Polls Tripo AI status. If SUCCEEDED, downloads the GLB and updates listing metadata.
    """
    from services.image_to_3d import get_task_status, download_and_save_glb
    
    listing = _get_listing_or_404(listing_id, db)
    user = get_user_by_username(db, current_user.username)
    if not user or (listing.owner_id != user.id and not user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorised")

    try:
        status_data = await get_task_status(task_id)
        
        if status_data["status"] == "SUCCEEDED":
            glb_remote_url = status_data["model_urls"].get("glb")
            if glb_remote_url:
                # Download and save locally
                unique_name = f"listing_{listing_id}_ai_{uuid.uuid4().hex[:8]}.glb"
                dest_path = AR_MODELS_DIR / unique_name
                success = await download_and_save_glb(glb_remote_url, str(dest_path))
                
                if success:
                    relative_url = f"/uploads/ar_models/{unique_name}"
                    listing.model_glb_url = relative_url
                    # Set a default polygon count for AI models if not provided
                    listing.polygon_count = status_data.get("polygon_count", 50000)
                    db.commit()
                    status_data["local_url"] = relative_url
        
        return status_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
