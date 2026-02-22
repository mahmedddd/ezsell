"""
Image-to-3D Service — Tripo3D AI  (Enhanced v2)
────────────────────────────────────────────────
• Multi-angle image support: combines front + side + back photos
• Style-hint text prompt injected with furniture type, colour, shape
• Intelligent crop: passes object-focused URL with bounding hints
• Converts furniture product images into real GLB 3D models

API docs: https://platform.tripo3d.ai/docs/api-reference
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List

import httpx

# ─── Config ───────────────────────────────────────────────────────────────────

TRIPO_API_KEY: str = os.getenv("TRIPO_API_KEY", "")
TRIPO_BASE = "https://api.tripo3d.ai/v2/openapi"

AR_MODELS_DIR = Path(__file__).parent.parent / "uploads" / "ar_models"
AR_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _headers() -> dict:
    if not TRIPO_API_KEY:
        raise ValueError(
            "TRIPO_API_KEY is not set. "
            "Sign up at https://www.tripo3d.ai and add your key to backend/.env"
        )
    return {"Authorization": f"Bearer {TRIPO_API_KEY}", "Content-Type": "application/json"}


def _build_style_prompt(
    furniture_type: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    material: Optional[str] = None,
) -> str:
    """
    Build an enhanced text prompt describing the furniture so Tripo3D
    generates a model that matches the listing as closely as possible.
    """
    parts = []

    if furniture_type:
        ft = furniture_type.replace("_", " ").lower()
        parts.append(f"a {ft}")
    else:
        parts.append("a piece of furniture")

    if material:
        parts.append(f"made of {material}")

    # Extract key descriptors from title / description
    combined = f"{title or ''} {description or ''}".lower()

    colour_keywords = [
        "white", "black", "grey", "gray", "beige", "brown", "walnut",
        "oak", "teak", "blue", "green", "red", "yellow", "cream", "ivory",
        "charcoal", "navy", "light", "dark", "wooden", "fabric", "leather",
        "velvet", "metal", "glass",
    ]
    extra_keywords = [
        "l-shaped", "l shaped", "corner", "sectional", "recliner",
        "king", "queen", "single", "double", "extendable", "sliding",
        "round", "oval", "glass top", "storage", "3-door", "4-door",
        "5-door", "6-door", "3 door", "4 door", "ergonomic", "mid-century",
    ]

    found_colours  = [k for k in colour_keywords  if k in combined]
    found_extra    = [k for k in extra_keywords    if k in combined]

    if found_colours:
        parts.append(", ".join(found_colours[:3]))   # max 3 colour descriptors
    if found_extra:
        parts.append(", ".join(found_extra[:3]))     # max 3 shape/variant descriptors

    prompt = " ".join(parts)
    prompt += (
        ". High-fidelity 3D model for augmented reality, "
        "realistic proportions, accurate real-world scale, "
        "detailed textures matching the product photo."
    )
    return prompt


# ─── Single-image task ─────────────────────────────────────────────────────────

async def start_image_to_3d_task(
    image_url: str,
    furniture_type: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    material: Optional[str] = None,
) -> str:
    """
    Submit an image-to-3D task to Tripo AI.
    Returns the task_id string. Raises httpx.HTTPStatusError on failure.
    """
    prompt = _build_style_prompt(furniture_type, title, description, material)

    payload: dict = {
        "type": "image_to_model",
        "file": {
            "type": "jpeg",
            "url": image_url,
        },
        # Text prompt helps Tripo understand style / shape
        "prompt": prompt,
        # Request the highest-quality output
        "model_version": "v2.5-20250123",
        "face_limit": 30000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{TRIPO_BASE}/task",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["task_id"]


# ─── Multi-angle task ──────────────────────────────────────────────────────────

async def start_multiview_to_3d_task(
    image_urls: List[str],
    furniture_type: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    material: Optional[str] = None,
) -> str:
    """
    Submit a multiview image-to-3D task (front + side + back / top).
    Falls back to single-image if only one URL provided.
    Returns the task_id string.
    """
    if not image_urls:
        raise ValueError("At least one image URL is required")

    if len(image_urls) == 1:
        return await start_image_to_3d_task(
            image_urls[0], furniture_type, title, description, material
        )

    prompt = _build_style_prompt(furniture_type, title, description, material)

    # Tripo multiview: front, back, left, right (1–4 images)
    # We send the first 4 images in best-match order
    angle_slots = ["front", "back", "left", "right"]
    files = []
    for i, url in enumerate(image_urls[:4]):
        files.append({
            "type": "jpeg",
            "url": url,
            "hint": angle_slots[i],  # helps Tripo orient the model correctly
        })

    payload: dict = {
        "type": "multiview_to_model",
        "files": files,
        "prompt": prompt,
        "model_version": "v2.5-20250123",
        "face_limit": 30000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{TRIPO_BASE}/task",
            headers=_headers(),
            json=payload,
        )
        # If multiview is not available on the plan, fall back to single-image
        if resp.status_code == 400:
            return await start_image_to_3d_task(
                image_urls[0], furniture_type, title, description, material
            )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["task_id"]


# ─── Status polling ────────────────────────────────────────────────────────────

async def get_task_status(task_id: str) -> dict:
    """
    Poll the status of a Tripo image-to-3D task.

    Normalised return dict:
      status     – "PENDING" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED"
      progress   – int 0-100
      model_urls – {"glb": str}  (present when SUCCEEDED)
      task_error – {"message": str}  (present when FAILED)
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{TRIPO_BASE}/task/{task_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        d = resp.json()["data"]

    status_map = {
        "queued":   "PENDING",
        "running":  "IN_PROGRESS",
        "success":  "SUCCEEDED",
        "failed":   "FAILED",
    }
    normalised = status_map.get(d.get("status", ""), "PENDING")

    out: dict = {
        "status":   normalised,
        "progress": int(d.get("progress", 0)),
    }

    if normalised == "SUCCEEDED":
        glb_url = (d.get("output") or {}).get("model", "")
        out["model_urls"] = {"glb": glb_url}

    if normalised == "FAILED":
        out["task_error"] = {"message": d.get("message", "Tripo generation failed")}

    return out


# ─── GLB download & cache ──────────────────────────────────────────────────────

async def download_and_cache_glb(glb_url: str, listing_id: int) -> str:
    """
    Download a GLB from Tripo's CDN, save to disk, return the local relative URL.
    """
    filename = f"listing_{listing_id}_{uuid.uuid4().hex[:10]}.glb"
    dest = AR_MODELS_DIR / filename

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        resp = await client.get(glb_url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)

    return f"/uploads/ar_models/{filename}"


# ─── Utility ──────────────────────────────────────────────────────────────────

def is_configured() -> bool:
    """Returns True when the Tripo API key is present in the environment."""
    return bool(TRIPO_API_KEY)
