import sqlite3
import os

db_path = 'c:/Users/ahmed/ezsell/ezsell/ezsell/backend/ezsell.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    # Try relative
    db_path = 'ezsell.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, phone FROM users WHERE username IN ('ahmed', 'test47');")
    rows = cursor.fetchall()
    print("User Data:")
    for row in rows:
        print(f"ID: {row[0]}, Username: {row[1]}, Phone: {row[2]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
