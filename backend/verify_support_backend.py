import requests
import json
from jose import jwt
import sys
import os

# Add the current directory to sys.path to import core.config
sys.path.append(os.getcwd())

try:
    from core.config import settings
except ImportError:
    # Fallback if import fails
    class MockSettings:
        SECRET_KEY = "a_very_secret_key_that_should_be_in_a_dotenv_file"
        ALGORITHM = "HS256"
        API_V1_STR = "/api/v1"
    settings = MockSettings()

BASE_URL = f"http://localhost:8000{settings.API_V1_STR}"

def create_test_token(username: str):
    return jwt.encode({"sub": username}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def test_support_flow():
    admin_username = "ahmed"
    token = create_test_token(admin_username)
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing as user: {admin_username}")
    
    # 1. Create a support ticket
    print("\n1. Creating a support ticket...")
    ticket_data = {
        "ticket_type": "bug",
        "subject": "Backend Test Bug",
        "description": "This is a test bug report from a script."
    }
    response = requests.post(f"{BASE_URL}/support/tickets", json=ticket_data, headers=headers)
    if response.status_code == 201:
        ticket = response.json()
        ticket_id = ticket['id']
        print(f"PASS: Ticket created with ID {ticket_id}")
    else:
        print(f"FAIL: Could not create ticket. Status: {response.status_code}, Body: {response.text}")
        return

    # 2. List all tickets (Admin only)
    print("\n2. Fetching all tickets (Admin)...")
    response = requests.get(f"{BASE_URL}/support/admin/tickets", headers=headers)
    if response.status_code == 200:
        tickets = response.json()
        print(f"PASS: Successfully fetched {len(tickets)} tickets")
        
        # Verify the ticket we just created is there and has user info
        my_ticket = next((t for t in tickets if t['id'] == ticket_id), None)
        if my_ticket:
            print(f"PASS: Found ticket {ticket_id} in admin list")
            if 'user' in my_ticket and my_ticket['user'] is not None:
                print(f"PASS: Ticket includes user info: {my_ticket['user']['username']}")
                if 'phone' in my_ticket['user']:
                    print(f"PASS: User info includes phone: {my_ticket['user']['phone']}")
            else:
                print("FAIL: Ticket DOES NOT include user info")
        else:
            print(f"FAIL: Ticket {ticket_id} not found in admin list")
    else:
        print(f"FAIL: Could not fetch admin tickets. Status: {response.status_code}, Body: {response.text}")

    # 3. Update ticket status
    print("\n3. Updating ticket status to 'working'...")
    update_data = {"status": "working"}
    response = requests.patch(f"{BASE_URL}/support/admin/tickets/{ticket_id}/status", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_ticket = response.json()
        print(f"PASS: Ticket status updated to {updated_ticket['status']}")
    else:
        print(f"FAIL: Could not update ticket status. Status: {response.status_code}, Body: {response.text}")

    # 4. Mark as done
    print("\n4. Marking ticket as 'done'...")
    update_data = {"status": "done"}
    response = requests.patch(f"{BASE_URL}/support/admin/tickets/{ticket_id}/status", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_ticket = response.json()
        print(f"PASS: Ticket status updated to {updated_ticket['status']}")
    else:
        print(f"FAIL: Could not update ticket status. Status: {response.status_code}, Body: {response.text}")

    # 5. Verify notification
    print("\n5. Verifying notification creation...")
    response = requests.get(f"{BASE_URL}/notifications", headers=headers)
    if response.status_code == 200:
        notifications = response.json()
        latest = notifications[0] if notifications else None
        if latest and "Ticket Status Updated" in latest['title'] and "Backend Test Bug" in latest['message']:
            print(f"PASS: Notification found: {latest['title']} - {latest['message']}")
            
            # 6. Mark as read
            print("\n6. Marking notification as read...")
            note_id = latest['id']
            response = requests.post(f"{BASE_URL}/notifications/{note_id}/read", headers=headers)
            if response.status_code == 200:
                print("PASS: Notification marked as read")
            else:
                print(f"FAIL: Could not mark as read. Status: {response.status_code}, Body: {response.text}")
        else:
            print(f"FAIL: Expected notification not found or content mismatch. Latest: {latest}")
    else:
        print(f"FAIL: Could not fetch notifications. Status: {response.status_code}")

if __name__ == "__main__":
    test_support_flow()
