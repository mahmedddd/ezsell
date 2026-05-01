import asyncio
import os
import json
import httpx
import sys
from pathlib import Path

# Add backend to path so we can import modules
sys.path.append(os.getcwd())

from core.config import settings

TRIPO_V2_BASE_URL = "https://api.tripo3d.ai/v2/openapi"

async def diagnose_all():
    print(f"TRIPO_API_KEY: {settings.TRIPO_API_KEY[:5]}...{settings.TRIPO_API_KEY[-5:]}")
    
    headers = {"Authorization": f"Bearer {settings.TRIPO_API_KEY}"}
    
    # 1. Check Balance First (Ensure key is valid)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{TRIPO_V2_BASE_URL}/user/balance", headers=headers)
        print(f"Balance Status: {r.status_code}")
        print(f"Balance Response: {r.text}")
        
    # 2. Upload Image
    test_img = r"uploads/listings/db5fef4f-a650-4746-9e8e-75c2783b2de3.png"
    if not os.path.exists(test_img):
        print(f"CRITICAL: {test_img} NOT FOUND")
        return
        
    print(f"Uploading {test_img}...")
    token = None
    async with httpx.AsyncClient() as client:
        with open(test_img, "rb") as f:
            files = {"file": f}
            r = await client.post(f"{TRIPO_V2_BASE_URL}/upload/sts", headers=headers, files=files)
            print(f"Upload Status: {r.status_code}")
            print(f"Upload Response: {r.text}")
            if r.status_code == 200:
                token = r.json()["data"]["image_token"]

    if not token:
        print("No task possible without token.")
        return

    # 3. Start task
    print(f"Starting task with token {token}...")
    payload = {
        "type": "image_to_model",
        "model_version": "v2.0-20240919",
        "input": {
            "file": {"file_token": token}
        }
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{TRIPO_V2_BASE_URL}/task", headers=headers, json=payload)
        print(f"Task Start Status: {r.status_code}")
        print(f"Task Start Response: {r.text}")

if __name__ == "__main__":
    asyncio.run(diagnose_all())
