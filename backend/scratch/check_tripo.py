import requests

url = "https://api.tripo3d.ai/v2/openapi/user/balance"
headers = {
    "Authorization": "Bearer tsk_z678EsT7eicLGc4wn4_z3EgZWBXJnTrYC1A1EGNVCtU"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
