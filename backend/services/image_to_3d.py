import httpx
import asyncio
import os
from typing import List, Optional, Dict, Any
from core.config import settings

TRIPO_V2_BASE_URL = "https://api.tripo3d.ai/v2/openapi"

async def upload_image_to_tripo(file_path: str) -> str:
    """Uploads a local image to Tripo AI and returns a file_token."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}"
    }
    
    url = f"{TRIPO_V2_BASE_URL}/upload/sts"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")

    # Determine file extension for V2 type requirement
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        ext = "jpg" # default fallback
    elif ext == "jpeg":
        ext = "jpg"

    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = await client.post(url, headers=headers, files=files)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Tripo upload failed: {data.get('message')}")
            # The token is returned in data["data"]["image_token"]
            return data["data"]["image_token"]

async def start_image_to_3d_task(
    image_url: Optional[str] = None,
    file_token: Optional[str] = None,
    model_version: str = "v2.0-20240919",
) -> str:
    """Starts a single-image to 3D task on Tripo3D V2 using flat payload."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    payload = {
        "type": "image_to_model",
        "model_version": model_version
    }
    
    if file_token:
        # V2 Requirement: Nest file_token in 'file' object with a type
        payload["file"] = {
            "type": "png", # Fallback to png as it's common for uploads
            "file_token": file_token
        }
    elif image_url:
        payload["file"] = {
            "type": "png",
            "url": image_url
        }
    else:
        raise ValueError("Either image_url or file_token must be provided")

    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRIPO_V2_BASE_URL}/task", json=payload, headers=headers)
        if response.status_code == 402 or (response.status_code == 200 and response.json().get("code") == 10006):
            raise Exception("Insufficient Tripo AI credits. Please top up your account.")
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"Tripo task creation failed: {data.get('message')}")
        return data["data"]["task_id"]

async def start_multiview_to_3d_task(
    image_urls: List[str] = None,
    file_tokens: List[str] = None,
    model_version: str = "v2.0-20240919",
    **kwargs
) -> str:
    """Starts a multi-view to 3D task on Tripo3D V2 using flat payload."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    payload = {
        "type": "multiview_to_model",
        "model_version": model_version,
        "files": [{}, {}, {}, {}] # [front, left, back, right]
    }
    
    if file_tokens:
        for i, token in enumerate(file_tokens[:4]):
            payload["files"][i] = {
                "type": "png",
                "file_token": token
            }
    elif image_urls:
        for i, url in enumerate(image_urls[:4]):
            payload["files"][i] = {
                "type": "png",
                "url": url
            }
    else:
        raise ValueError("Either image_urls or file_tokens must be provided")

    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRIPO_V2_BASE_URL}/task", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"Tripo multiview task failed: {data.get('message')}")
        return data["data"]["task_id"]

async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Polls the status of a Tripo3D V2 task."""
    if not settings.TRIPO_API_KEY:
        raise ValueError("TRIPO_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.TRIPO_API_KEY}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TRIPO_V2_BASE_URL}/task/{task_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            raise Exception(f"Tripo status check failed: {data.get('message')}")
            
        task_data = data["data"]
        
        # Tripo V2 uses "success" but backend expects "SUCCEEDED"
        status_mapped = task_data.get("status", "")
        if status_mapped == "success":
            status_mapped = "SUCCEEDED"
            
        # V2 stores the GLB url in output.pbr_model or result.pbr_model.url
        pbr_url = task_data.get("output", {}).get("pbr_model")
        if not pbr_url and "result" in task_data:
            pbr_url = task_data["result"].get("pbr_model", {}).get("url")
            
        model_urls = {"glb": pbr_url} if pbr_url else {}

        return {
            "task_id": task_data["task_id"],
            "status": status_mapped,
            "progress": task_data.get("progress", 0),
            "model_urls": model_urls,
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
