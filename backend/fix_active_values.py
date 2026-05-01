
import sqlite3

def check_active_values():
    conn = sqlite3.connect('ezsell.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, is_active FROM listings")
    rows = cursor.fetchall()
    print("Listings and their 'is_active' status:")
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1]}, Active: {row[2]}")
        
    # Check for NULLs or False
    cursor.execute("SELECT COUNT(*) FROM listings WHERE is_active IS NULL OR is_active = 0")
    count = cursor.fetchone()[0]
    print(f"\nFound {count} listings with is_active = NULL or 0.")
    
    if count > 0:
        print("Updating all listings to is_active = 1...")
        cursor.execute("UPDATE listings SET is_active = 1")
        conn.commit()
        print("Updated successfully.")
        
    conn.close()

if __name__ == "__main__":
    check_active_values()
