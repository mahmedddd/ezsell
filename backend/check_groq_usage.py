import httpx
import os
from dotenv import load_dotenv

# Load environment variables from the backend .env file
load_dotenv(dotenv_path='c:/Users/ahmed/ezsell/backend/.env')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def check_groq_limits():
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in .env")
        return

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    # Using the exact model from the app
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response Body: {response.text}")
            
            # Extract rate limit headers
            headers = response.headers
            # Groq headers are usually x-ratelimit-*
            limits = {
                "Requests Limit": headers.get("x-ratelimit-limit-requests"),
                "Requests Remaining": headers.get("x-ratelimit-remaining-requests"),
                "Requests Reset": headers.get("x-ratelimit-reset-requests"),
                "Tokens Limit": headers.get("x-ratelimit-limit-tokens"),
                "Tokens Remaining": headers.get("x-ratelimit-remaining-tokens"),
                "Tokens Reset": headers.get("x-ratelimit-reset-tokens"),
            }
            
            print("\nGroq Rate Limit Status:")
            for key, value in limits.items():
                if value:
                    print(f"{key}: {value}")
                
            if response.status_code == 429:
                print("\nALERT: You are currently rate limited!")
                
    except Exception as e:
        print(f"Error checking Groq limits: {e}")

import asyncio
if __name__ == "__main__":
    asyncio.run(check_groq_limits())
