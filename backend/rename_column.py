import sqlite3
import os

db_path = 'ezsell.db'
if not os.path.exists(db_path):
    print("Database not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if profile_picture exists
    cursor.execute("SELECT profile_picture FROM users LIMIT 1")
    print("Renaming 'profile_picture' to 'avatar_url'...")
    
    # SQLite doesn't support RENAME COLUMN in older versions (< 3.25.0)
    # But since this is a new project, we can try RENAME COLUMN or use the standard migration pattern
    try:
        cursor.execute("ALTER TABLE users RENAME COLUMN profile_picture TO avatar_url")
        print("Column renamed successfully via ALTER TABLE.")
    except sqlite3.OperationalError as e:
        print(f"ALTER TABLE failed: {e}. Falling back to manual migration...")
        # Fallback for older SQLite: create new table, copy data, drop old table, rename new table
        # But usually in dev, we can just add a new column and copy data if RENAME fails
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        cursor.execute("UPDATE users SET avatar_url = profile_picture")
        print("Data copied to 'avatar_url'. Note: 'profile_picture' column still exists but is unused.")

    conn.commit()
    print("Migration complete!")
except sqlite3.OperationalError:
    print("Column 'profile_picture' not found. It might already be renamed or doesn't exist.")

conn.close()
