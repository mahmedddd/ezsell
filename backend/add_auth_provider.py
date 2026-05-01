import sqlite3
import os

db_path = 'ezsell.db'
if not os.path.exists(db_path):
    print("Database not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT auth_provider FROM users LIMIT 1")
    print("Column 'auth_provider' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'auth_provider' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")
    conn.commit()
    print("Column 'auth_provider' added successfully.")

conn.close()
