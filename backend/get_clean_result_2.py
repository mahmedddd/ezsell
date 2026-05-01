import asyncio
import httpx
import sys
import os
import json

sys.path.append(os.getcwd())
from core.config import settings

TRIPO_V2_BASE_URL = "https://api.tripo3d.ai/v2/openapi"

async def test_polling():
    headers = {"Authorization": f"Bearer {settings.TRIPO_API_KEY}"}
    
    img = "uploads/listings/db5fef4f-a650-4746-9e8e-75c2783b2de3.png"
    async with httpx.AsyncClient() as client:
        with open(img, "rb") as f:
            ru = await client.post(f"{TRIPO_V2_BASE_URL}/upload/sts", headers=headers, files={"file": f})
            token = ru.json()["data"]["image_token"]
            
    p = {
        "type": "image_to_model",
        "file": {
            "type": "png",
            "file_token": token
        }
    }
    async with httpx.AsyncClient() as client:
        rt = await client.post(f"{TRIPO_V2_BASE_URL}/task", headers=headers, json=p)
        task_id = rt.json()["data"]["task_id"]
        
    print(f"Polling {task_id}...")
    
    async with httpx.AsyncClient() as client:
        for i in range(40):
            rp = await client.get(f"{TRIPO_V2_BASE_URL}/task/{task_id}", headers=headers)
            try:
                task_data = rp.json().get("data", {})
                status = task_data.get("status")
            except Exception:
                continue
                
            if status in ["success", "SUCCEEDED", "failed", "FAILED"]:
                with open("success.json", "w") as f:
                    json.dump(task_data, f, indent=2)
                print("SAVED success.json")
                break
                
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(test_polling())
