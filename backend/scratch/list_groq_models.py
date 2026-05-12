from groq import Groq
import os

def list_models(api_key):
    try:
        client = Groq(api_key=api_key)
        models = client.models.list()
        print("Available Models:")
        for m in models.data:
            print(f"- {m.id}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("GROQ_API_KEY")
    if key:
        list_models(key)
    else:
        print("GROQ_API_KEY not found in .env")
