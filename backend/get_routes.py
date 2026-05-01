import requests

try:
    resp = requests.get("http://localhost:8000/api/v1/openapi.json")
    resp.raise_for_status()
    data = resp.json()
    paths = data.get("paths", {}).keys()
    
    login_paths = [p for p in paths if "login" in p.lower()]
    conv_paths = [p for p in paths if "conversation" in p.lower()]
    
    print("Login paths:", login_paths)
    print("Conversation paths:", conv_paths)
except Exception as e:
    print(f"Error: {e}")
