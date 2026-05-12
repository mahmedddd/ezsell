import os
from groq import Groq

def check_groq_limits(api_key):
    try:
        client = Groq(api_key=api_key)
        # We make a tiny request to get the rate limit headers
        response = client.chat.completions.with_raw_response.create(
            messages=[{"role": "user", "content": "hi"}],
            model="llama-3.3-70b-versatile",
            max_tokens=1
        )
        
        headers = response.headers
        print("--- Groq Rate Limit Info ---")
        # Standard rate limit headers for Groq
        print(f"Requests Limit (RPM): {headers.get('x-ratelimit-limit-requests')}")
        print(f"Requests Remaining: {headers.get('x-ratelimit-remaining-requests')}")
        print(f"Tokens Limit (TPM): {headers.get('x-ratelimit-limit-tokens')}")
        print(f"Tokens Remaining: {headers.get('x-ratelimit-remaining-tokens')}")
        print(f"Tokens Reset in: {headers.get('x-ratelimit-reset-tokens')}")
        print(f"Requests Reset in: {headers.get('x-ratelimit-reset-requests')}")
        
    except Exception as e:
        print(f"Error checking Groq limits: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("GROQ_API_KEY")
    if key:
        check_groq_limits(key)
    else:
        print("GROQ_API_KEY not found in .env")
