import sqlite3
import os

db_path = 'c:/Users/ahmed/ezsell/ezsell/ezsell/backend/ezsell.db'
if not os.path.exists(db_path):
    db_path = 'ezsell.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check all listings and their owners
    query = """
    SELECT l.id, l.title, l.owner_id, u.username, u.phone 
    FROM listings l
    JOIN users u ON l.owner_id = u.id
    LIMIT 20;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("Listing-Owner Data:")
    for row in rows:
        print(f"LID: {row[0]}, Title: {row[1]}, OID: {row[2]}, Owner: {row[3]}, Phone: {row[4]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
