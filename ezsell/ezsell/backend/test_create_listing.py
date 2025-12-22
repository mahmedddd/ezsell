import requests

# First, create a test user and login
register_data = {
    "username": "testuser123",
    "email": "test123@test.com",
    "password": "test123456",
    "full_name": "Test User"
}

print("1. Registering test user...")
try:
    r = requests.post('http://localhost:8000/api/v1/register', json=register_data, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 400:
        print("   User already exists, trying to login...")
except Exception as e:
    print(f"   Error: {e}")

# Login
print("\n2. Logging in...")
login_data = {
    "username": "testuser123",
    "password": "test123456"
}
try:
    r = requests.post('http://localhost:8000/api/v1/login', json=login_data, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        token = r.json().get('access_token')
        print(f"   Token: {token[:50]}...")
    else:
        print(f"   Error: {r.text}")
        exit(1)
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# Create listing with image
print("\n3. Creating listing...")
headers = {'Authorization': f'Bearer {token}'}
files = {'images': ('test.jpg', b'fake-image-data', 'image/jpeg')}
data = {
    'title': 'Samsung Galaxy S23 Ultra',
    'description': 'Brand new phone in excellent condition',
    'category': 'mobile',
    'price': '150000',
    'condition': 'new',
    'location': 'Lahore',
    'brand': 'Samsung'
}

try:
    r = requests.post('http://localhost:8000/api/v1/listings', 
                     headers=headers, 
                     files=files, 
                     data=data,
                     timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:500]}")
except requests.exceptions.Timeout:
    print("   ERROR: Request timed out!")
except requests.exceptions.ConnectionError as e:
    print(f"   ERROR: Connection error - {str(e)[:200]}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__} - {str(e)[:200]}")
