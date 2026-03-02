import sqlite3
import os

db_path = 'c:/Users/ahmed/ezsell/ezsell/ezsell/backend/ezsell.db'
if not os.path.exists(db_path):
    db_path = 'ezsell.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update phone numbers
    cursor.execute("UPDATE users SET phone='+923355369632' WHERE username='ahmed'")
    cursor.execute("UPDATE users SET phone='+923001234567' WHERE username='test47'")
    
    conn.commit()
    print("Successfully updated phone numbers for ahmed and test47")
    
    # Verify
    cursor.execute("SELECT id, username, phone FROM users WHERE username IN ('ahmed', 'test47')")
    rows = cursor.fetchall()
    for row in rows:
        print(f"User: {row[1]}, Phone: {row[2]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
