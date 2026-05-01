
import sqlite3

def check_schema():
    conn = sqlite3.connect('ezsell.db')
    cursor = conn.cursor()
    
    # Table Info
    cursor.execute("PRAGMA table_info(listings)")
    columns = cursor.fetchall()
    print("Listing Table Columns:")
    for col in columns:
        print(f"ID: {col[0]}, Name: {col[1]}, Type: {col[2]}, Default: {col[4]}")
        
    # Sample Row
    cursor.execute("SELECT * FROM listings LIMIT 1")
    row = cursor.fetchone()
    if row:
        desc = cursor.description
        print("\nSample Listing Row:")
        for i in range(len(desc)):
            print(f"{desc[i][0]}: {row[i]}")
    else:
        print("\nNo listings found in DB.")
        
    # Check all owners
    cursor.execute("SELECT DISTINCT owner_id FROM listings")
    owners = cursor.fetchall()
    print(f"\nExisting Owner IDs in Listings: {owners}")

    conn.close()

if __name__ == "__main__":
    check_schema()
