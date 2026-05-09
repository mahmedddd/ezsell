import httpx
import asyncio

async def check_groq_limits(api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
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
                return
            
            headers = response.headers
            limits = {
                "Requests Limit": headers.get("x-ratelimit-limit-requests"),
                "Requests Remaining": headers.get("x-ratelimit-remaining-requests"),
                "Requests Reset": headers.get("x-ratelimit-reset-requests"),
                "Tokens Limit": headers.get("x-ratelimit-limit-tokens"),
                "Tokens Remaining": headers.get("x-ratelimit-remaining-tokens"),
                "Tokens Reset": headers.get("x-ratelimit-reset-tokens"),
            }
            
            print("\nGroq Rate Limit Status (New Key):")
            for key, value in limits.items():
                if value:
                    print(f"{key}: {value}")
                
    except Exception as e:
        print(f"Error checking Groq limits: {e}")

if __name__ == "__main__":
    new_key = "gsk_your_api_key_here"
    asyncio.run(check_groq_limits(new_key))
