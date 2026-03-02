import httpx
import asyncio
from typing import List, Optional, Dict, Any
from core.config import settings

TRIPO_API_URL = "https://api.tripo3d.ai/v1/task"

async def start_image_to_3d_task(
    image_url: str,
    model_version: str = "v1.4-20240625",
) -> str:
    """Starts a single-image to 3D task on Tripo3D."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    payload = {
        "type": "image_to_model",
        "model_version": model_version,
        "input": {
            "image_url": image_url
        }
    }
    
    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TRIPO_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["data"]["task_id"]

async def start_multiview_to_3d_task(
    image_urls: List[str],
    model_version: str = "v1.4-20240625",
    **kwargs
) -> str:
    """Starts a multi-view to 3D task on Tripo3D."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    payload = {
        "type": "multiview_to_model",
        "model_version": model_version,
        "input": {
            "image_urls": image_urls
        }
    }
    
    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TRIPO_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["data"]["task_id"]

async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Polls the status of a Tripo3D task."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TRIPO_API_URL}/{task_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        # Format the response consistently for the frontend
        task_data = data["data"]
        return {
            "task_id": task_data["task_id"],
            "status": task_data["status"],
            "progress": task_data.get("progress", 0),
            "model_urls": task_data.get("output", {}),
            "error": task_data.get("error")
        }

async def download_and_save_glb(url: str, dest_path: str) -> bool:
    """Downloads a GLB from a URL and saves it to a local path."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"❌ [IMAGE_TO_3D] Failed to download GLB: {e}")
        return False
