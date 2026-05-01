import sqlite3
import os

db_path = 'ezsell.db'
if not os.path.exists(db_path):
    print("Database not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check and add columns to users table
try:
    cursor.execute("SELECT phone FROM users LIMIT 1")
    print("Column 'phone' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'phone' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

try:
    cursor.execute("SELECT bio FROM users LIMIT 1")
    print("Column 'bio' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'bio' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")

try:
    cursor.execute("SELECT location FROM users LIMIT 1")
    print("Column 'location' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'location' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN location TEXT")

try:
    cursor.execute("SELECT google_id FROM users LIMIT 1")
    print("Column 'google_id' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'google_id' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")

try:
    cursor.execute("SELECT avatar_url FROM users LIMIT 1")
    print("Column 'avatar_url' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'avatar_url' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")

try:
    cursor.execute("SELECT last_login FROM users LIMIT 1")
    print("Column 'last_login' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'last_login' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")

try:
    cursor.execute("SELECT auth_provider FROM users LIMIT 1")
    print("Column 'auth_provider' already exists.")
except sqlite3.OperationalError:
    print("Adding column 'auth_provider' to 'users' table...")
    cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")

# SupportTicket table
try:
    cursor.execute("SELECT id FROM support_tickets LIMIT 1")
    print("Table 'support_tickets' already exists.")
except sqlite3.OperationalError:
    print("Creating 'support_tickets' table...")
    cursor.execute("""
    CREATE TABLE support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticket_type TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        attachment_url TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

# Reset 'ahmed' password and ensure admin status
try:
    from bcrypt import hashpw, gensalt
    hashed_pass = hashpw(b"ahmed123", gensalt()).decode('utf-8')
    cursor.execute("UPDATE users SET hashed_password = ?, is_admin = 1 WHERE username = 'ahmed'", (hashed_pass,))
    if cursor.rowcount == 0:
        print("User 'ahmed' not found, creating...")
        cursor.execute("INSERT INTO users (username, email, hashed_password, full_name, is_admin, phone, is_verified) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('ahmed', 'ahmed@example.com', hashed_pass, 'Ahmed Ali', 1, '+92000000000', 1))
    print("User 'ahmed' updated/created with password 'ahmed123' and admin status.")
except ImportError:
    print("Bcrypt not found, skipping password reset.")

conn.commit()
conn.close()
print("Database schema update complete!")
