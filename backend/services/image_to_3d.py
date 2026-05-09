import httpx
import asyncio
import os
import subprocess
import shutil
from typing import List, Optional, Dict, Any
from core.config import settings

TRIPO_V2_BASE_URL = "https://api.tripo3d.ai/v2/openapi"


async def optimize_glb_with_draco(glb_path: str) -> bool:
    """
    Applies Draco mesh compression to a GLB file using gltf-transform CLI.
    Draco is LOSSLESS geometry compression — zero visual quality change.
    It dramatically reduces GPU memory bandwidth, fixing iPhone XR thermal throttling.
    
    Requires: npx (comes with Node.js, already installed for npm build)
    Returns True if optimization succeeded, False if it failed (original file kept).
    """
    try:
        original_size = os.path.getsize(glb_path)
        temp_path = glb_path + ".optimized.glb"
        
        print(f"🔧 [GLB_OPT] Optimizing {os.path.basename(glb_path)} ({original_size / 1024:.0f} KB) with Draco...")
        
        result = subprocess.run(
            [
                "npx", "--yes", "@gltf-transform/cli",
                "optimize",
                glb_path,
                temp_path,
                "--compress", "draco",       # Draco mesh compression (lossless geometry)
                "--simplify", "false",        # Do NOT simplify mesh — keeps full visual quality
                "--flatten", "false",         # Keep scene graph intact
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for large models
        )
        
        if result.returncode == 0 and os.path.exists(temp_path):
            optimized_size = os.path.getsize(temp_path)
            
            # Only replace if the optimized file is valid and smaller
            if optimized_size > 1024:  # Must be at least 1KB to be valid
                shutil.move(temp_path, glb_path)
                saving_pct = (1 - optimized_size / original_size) * 100
                print(f"✅ [GLB_OPT] Draco compression done: {original_size / 1024:.0f} KB → {optimized_size / 1024:.0f} KB ({saving_pct:.0f}% smaller)")
                return True
            else:
                os.remove(temp_path)
                print(f"⚠️ [GLB_OPT] Optimized file too small, keeping original")
                return False
        else:
            print(f"⚠️ [GLB_OPT] gltf-transform failed (rc={result.returncode}): {result.stderr[:200]}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️ [GLB_OPT] Optimization timed out, keeping original file")
        return False
    except FileNotFoundError:
        print(f"⚠️ [GLB_OPT] npx not found — skipping Draco compression")
        return False
    except Exception as e:
        print(f"⚠️ [GLB_OPT] Optimization error: {e}")
        return False


async def download_and_save_glb(url: str, dest_path: str) -> bool:
    """Downloads a GLB from a URL, saves it, then applies Draco compression."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=120.0)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(response.content)
        
        raw_size = os.path.getsize(dest_path)
        print(f"✅ [IMAGE_TO_3D] GLB downloaded: {dest_path} ({raw_size / 1024:.0f} KB)")
        
        # Apply Draco compression in a thread to not block the event loop
        # This is safe — it's a separate process, zero visual quality change
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: asyncio.run(optimize_glb_with_draco(dest_path))
        )
        
        return True
    except Exception as e:
        print(f"❌ [IMAGE_TO_3D] Failed to download GLB: {e}")
        return False


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
            if response.status_code in [402, 403] or (response.status_code == 200 and response.json().get("code") == 10006):
                raise Exception("Insufficient Tripo AI credits or invalid API key. Please top up your account.")
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
        if response.status_code in [402, 403] or (response.status_code == 200 and response.json().get("code") == 10006):
            raise Exception("Insufficient Tripo AI credits or invalid API key. Please top up your account.")
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
        if response.status_code in [402, 403] or (response.status_code == 200 and response.json().get("code") == 10006):
            raise Exception("Insufficient Tripo AI credits or invalid API key. Please top up your account.")
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
        
        # Tripo V2 uses lowercase statuses like "success", "failed", "queued", "running"
        status_mapped = task_data.get("status", "").upper()
        if status_mapped == "SUCCESS":
            status_mapped = "SUCCEEDED"
            
        # Tripo V2 stores the GLB url in output.model or output.pbr_model or result.model.url
        pbr_url = None
        output = task_data.get("output", {})
        result = task_data.get("result", {})
        
        if isinstance(output, dict):
            pbr_url = output.get("model") or output.get("pbr_model") or output.get("base_model")
            
        if not pbr_url and isinstance(result, dict):
            pbr_url = (
                result.get("model", {}).get("url") or 
                result.get("pbr_model", {}).get("url") or 
                result.get("base_model", {}).get("url")
            )
            
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
