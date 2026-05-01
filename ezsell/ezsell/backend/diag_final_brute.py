import asyncio
import os
import json
import httpx
import sys

# Correct key provided by user
TRIPO_KEY = "tsk_z678EsT7eicLGc4wn4_z3EgZWBXJnTrYC1A1EGNVCtU"
U_URL = "https://api.tripo3d.ai/v2/openapi/upload/sts"
T_URL = "https://api.tripo3d.ai/v2/openapi/task"

async def main():
    h = {"Authorization": f"Bearer {TRIPO_KEY}"}
    async with httpx.AsyncClient() as client:
        # 1. Upload
        img = "uploads/listings/db5fef4f-a650-4746-9e8e-75c2783b2de3.png"
        with open(img, "rb") as f:
            ru = await client.post(U_URL, headers=h, files={"file": f})
            token = ru.json()["data"]["image_token"]
            
        # 2. Try various task types
        types = ["image_to_model", "IMAGE_TO_MODEL", "image_to_3d", "IMAGE_TO_3D"]
        for t in types:
            print(f"Testing Type: {t}")
            p = {
                "type": t,
                "input": {"file": {"file_token": token}}
            }
            rt = await client.post(T_URL, headers=h, json=p)
            print(f"Response ({t}): {rt.text}")

if __name__ == "__main__":
    asyncio.run(main())
