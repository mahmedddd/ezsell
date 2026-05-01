import httpx
import asyncio
import os
import json

TRIPO_API_KEY = "tsk_z678EsT7eicLGc4wn4_z3EgZWBXJnTrYC1A1EGNVCtU"
TASKS_URL = "https://api.tripo3d.ai/v2/openapi/task"

async def check_recent_tasks():
    headers = {"Authorization": f"Bearer {TRIPO_API_KEY}"}
    async with httpx.AsyncClient() as client:
        # Get multiple to see history
        r = await client.get(f"{TASKS_URL}?limit=5", headers=headers)
        print(f"Status: {r.status_code}")
        data = r.json()
        if data.get("code") == 0:
            tasks = data["data"].get("tasks", [])
            print(f"Found {len(tasks)} tasks:")
            for t in tasks:
                print(f"ID: {t['task_id']} | Type: {t['type']} | Status: {t['status']} | Progress: {t.get('progress')}% | Created: {t.get('created_at')}")
        else:
            print(f"Error: {data.get('message')}")

if __name__ == "__main__":
    asyncio.run(check_recent_tasks())
