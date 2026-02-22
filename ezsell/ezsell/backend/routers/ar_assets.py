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

# Image-to-3D AI service (Tripo3D) — imported lazily so missing key doesn't break startup
try:
    from services.image_to_3d import (
        start_image_to_3d_task,
        start_multiview_to_3d_task,
        get_task_status as meshy_get_status,
        download_and_cache_glb,
        is_configured as meshy_is_configured,
    )
    _IMAGE_TO_3D_AVAILABLE = True
except ImportError:
    _IMAGE_TO_3D_AVAILABLE = False

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


# ─── AI Image-to-3D Endpoints (Tripo3D) ─────────────────────────────────────

@router.post("/products/{listing_id}/generate-3d", status_code=status.HTTP_202_ACCEPTED)
async def start_generate_3d(
    listing_id: int,
    image_url: str = Query(..., description="Primary product image URL"),
    # Optional: comma-separated list of additional angle image URLs
    extra_image_urls: Optional[str] = Query(
        None,
        description="Comma-separated additional angle image URLs (side, back, top) for higher-accuracy multi-view generation"
    ),
    db: Session = Depends(get_db),
):
    """
    **Public** endpoint — starts an AI image-to-3D task via Tripo3D.

    • Accepts an optional `extra_image_urls` comma-separated list so the caller
      can pass side / back / top photos for a much higher-fidelity 3-D model.
    • Reads listing title/description/furniture_type/material and injects them
      as a text prompt so Tripo3D understands the shape and material of the item.

    The frontend polls `/products/{id}/generate-3d/{task_id}` every 3 s until
    status is `complete` or `failed`.

    Requires `TRIPO_API_KEY` in the backend `.env` file.
    Sign up at https://www.tripo3d.ai — free credits on every new account.
    """
    if not _IMAGE_TO_3D_AVAILABLE:
        raise HTTPException(status_code=503, detail="image_to_3d service not available (import error)")

    if not meshy_is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI 3D generation is not configured. "
                "Add TRIPO_API_KEY=<your_key> to backend/.env — "
                "sign up free at https://www.tripo3d.ai"
            ),
        )

    _ensure_ar_columns(db)
    listing = _get_listing_or_404(listing_id, db)

    if listing.category.lower() != "furniture":
        raise HTTPException(status_code=400, detail="AI 3D generation is only for furniture listings")

    # Build list of all angles (primary first, then extra)
    all_urls = [image_url]
    if extra_image_urls:
        extras = [u.strip() for u in extra_image_urls.split(",") if u.strip()]
        all_urls.extend(extras)

    # Gather listing metadata for Tripo3D style prompt
    furniture_type = getattr(listing, "furniture_type", None)
    title         = getattr(listing, "title", None)
    description   = getattr(listing, "description", None)
    material      = getattr(listing, "material", None)

    try:
        if len(all_urls) > 1:
            task_id = await start_multiview_to_3d_task(
                all_urls,
                furniture_type=furniture_type,
                title=title,
                description=description,
                material=material,
            )
            mode = "multiview"
        else:
            task_id = await start_image_to_3d_task(
                image_url,
                furniture_type=furniture_type,
                title=title,
                description=description,
                material=material,
            )
            mode = "single"
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tripo API error: {exc}") from exc

    return {
        "task_id":    task_id,
        "status":     "pending",
        "listing_id": listing_id,
        "mode":       mode,
        "image_count": len(all_urls),
    }


@router.get("/products/{listing_id}/generate-3d/{task_id}")
async def poll_generate_3d(
    listing_id: int,
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    **Public** endpoint — polls the AI image-to-3D task.

    When `status == "complete"` the GLB is downloaded, cached, and the listing's
    `model_glb_url` is updated so subsequent viewers get the AI model instantly.

    Response shape:
        {status: "pending"|"processing"|"complete"|"failed",
         progress: 0-100, glb_url?: string, error?: string}
    """
    if not _IMAGE_TO_3D_AVAILABLE:
        raise HTTPException(status_code=503, detail="image_to_3d service not available")

    _ensure_ar_columns(db)
    listing = _get_listing_or_404(listing_id, db)

    try:
        result = await meshy_get_status(task_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tripo API error: {exc}") from exc

    meshy_status: str = result.get("status", "PENDING")
    progress: int = int(result.get("progress", 0))

    if meshy_status == "SUCCEEDED":
        glb_cdn_url = (result.get("model_urls") or {}).get("glb", "")
        if not glb_cdn_url:
            return {"status": "failed", "progress": 0, "error": "Tripo returned no GLB URL"}

        # Download & cache locally (so the GLB survives CDN expiry)
        try:
            local_url = await download_and_cache_glb(glb_cdn_url, listing_id)
        except Exception:
            local_url = glb_cdn_url

        # Persist to DB so next page-load skips generation entirely
        listing.model_glb_url = local_url
        db.commit()
        db.refresh(listing)

        return {
            "status":   "complete",
            "progress": 100,
            "glb_url":  local_url,
            **_serialize_assets(listing),
        }

    if meshy_status == "FAILED":
        err_msg = (result.get("task_error") or {}).get("message", "Unknown Tripo error")
        return {"status": "failed", "progress": 0, "error": err_msg}

    # PENDING or IN_PROGRESS
    return {"status": "processing", "progress": progress}
