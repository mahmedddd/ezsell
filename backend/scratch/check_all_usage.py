import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='c:/Users/ahmed/ezsell/backend/.env')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TRIPO_API_KEY = os.getenv("TRIPO_API_KEY")

async def check_groq(model):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                h = r.headers
                return {
                    "model": model,
                    "remaining_requests": h.get("x-ratelimit-remaining-requests"),
                    "remaining_tokens": h.get("x-ratelimit-remaining-tokens"),
                    "reset_tokens": h.get("x-ratelimit-reset-tokens")
                }
            return {"model": model, "error": r.text}
        except Exception as e:
            return {"model": model, "error": str(e)}

async def check_tripo():
    # V2 Balance check is actually at /user/balance
    url = "https://api.tripo3d.ai/v2/openapi/user/balance"
    headers = {"Authorization": f"Bearer {TRIPO_API_KEY}"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == 0:
                    return data["data"]
            return {"error": r.text}
        except Exception as e:
            return {"error": str(e)}

async def main():
    print("--- GROQ STATUS ---")
    results = await asyncio.gather(
        check_groq("llama-3.3-70b-versatile"),
        check_groq("llama-3.1-8b-instant")
    )
    for res in results:
        print(res)
    
    print("\n--- TRIPO STATUS ---")
    tripo = await check_tripo()
    print(tripo)

if __name__ == "__main__":
    asyncio.run(main())
