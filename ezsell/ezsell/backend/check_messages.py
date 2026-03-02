import sqlite3
import os

db_path = 'c:/Users/ahmed/ezsell/ezsell/ezsell/backend/ezsell.db'
if not os.path.exists(db_path):
    db_path = 'ezsell.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check messages
    print("Recent messages:")
    cursor.execute("SELECT m.id, u1.username as sender, u2.username as receiver, m.content, m.created_at FROM messages m JOIN users u1 ON m.sender_id = u1.id JOIN users u2 ON m.receiver_id = u2.id ORDER BY m.created_at DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, From: {row[1]}, To: {row[2]}, Content: {row[3][:30]}..., Created: {row[4]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
