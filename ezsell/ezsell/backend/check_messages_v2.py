import sqlite3
import os

db_path = 'c:/Users/ahmed/ezsell/ezsell/ezsell/backend/ezsell.db'
if not os.path.exists(db_path):
    db_path = 'ezsell.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check messages columns
    cursor.execute("PRAGMA table_info(messages)")
    cols = cursor.fetchall()
    print("Messages columns:", [c[1] for c in cols])
    
    # Check messages with listing info
    print("\nRecent messages with listing info:")
    cursor.execute("""
        SELECT m.id, u1.username as sender, u2.username as receiver, m.listing_id, m.content, m.created_at 
        FROM messages m 
        JOIN users u1 ON m.sender_id = u1.id 
        JOIN users u2 ON m.receiver_id = u2.id 
        ORDER BY m.created_at DESC 
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, From: {row[1]}, To: {row[2]}, Listing: {row[3]}, Content: {row[4][:30]}..., Created: {row[5]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
