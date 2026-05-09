import httpx
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='c:/Users/ahmed/ezsell/backend/.env')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def check_model(model_name):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_name, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"\n--- Model: {model_name} ---")
            print(f"Status: {response.status_code}")
            h = response.headers
            print(f"Requests: {h.get('x-ratelimit-remaining-requests')}/{h.get('x-ratelimit-limit-requests')} (Reset: {h.get('x-ratelimit-reset-requests')})")
            print(f"Tokens: {h.get('x-ratelimit-remaining-tokens')}/{h.get('x-ratelimit-limit-tokens')} (Reset: {h.get('x-ratelimit-reset-tokens')})")
            # Some tiers show TPD in specific headers or the body on error
    except Exception as e:
        print(f"Error: {e}")

async def main():
    await check_model("llama-3.3-70b-versatile")
    await check_model("llama-3.1-8b-instant")

import asyncio
asyncio.run(main())
