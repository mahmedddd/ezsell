
import sqlite3

def fix_all_listings():
    conn = sqlite3.connect('ezsell.db')
    cursor = conn.cursor()
    
    # 1. Ensure all listings are explicitly active and approved (except the one pending)
    # Most of your listings were 'pending' which is why they were hidden
    print("Updating listings to 'approved' and 'is_active=1'...")
    cursor.execute("UPDATE listings SET is_active = 1, approval_status = 'approved' WHERE approval_status = 'pending' AND title NOT LIKE '%wooden king size bed%'")
    conn.commit()
    
    # 2. Check current status
    cursor.execute("SELECT id, title, is_active, approval_status FROM listings")
    rows = cursor.fetchall()
    print("\nFinal Database State:")
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1]}, Active: {row[2]}, Status: {row[3]}")
        
    conn.close()

if __name__ == "__main__":
    fix_all_listings()
