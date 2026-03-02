import sqlite3

def upgrade_database():
    """Manual SQLite migration to add missing columns"""
    print("Connecting to database...")
    conn = sqlite3.connect('ezsell.db')
    cursor = conn.cursor()
    
    # 1. Upgrade 'listings' table
    listings_cols = [
        ('furniture_type', 'TEXT'),
        ('material', 'TEXT'),
        ('furniture_subtype', 'TEXT'),
        ('furniture_brand', 'TEXT'),
        ('is_sliding_door', 'INTEGER DEFAULT 0'),
        ('has_mattress', 'INTEGER DEFAULT 0'),
        ('mattress_type', 'TEXT'),
        ('predicted_price', 'REAL'),
        ('confidence_score', 'REAL'),
        ('listing_hash', 'TEXT'),
        ('fraud_flags', 'TEXT'),
        ('rejection_reason', 'TEXT'),
        ('semantic_embedding', 'TEXT')
    ]
    
    for col_name, col_type in listings_cols:
        try:
            print(f"Adding {col_name} to listings...")
            cursor.execute(f"ALTER TABLE listings ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Already exists
            else:
                print(f"Error adding {col_name} to listings: {e}")

    # 2. Upgrade 'furniture' table
    furniture_cols = [
        ('furniture_brand', 'TEXT'),
        ('is_sliding_door', 'INTEGER DEFAULT 0'),
        ('has_mattress', 'INTEGER DEFAULT 0'),
        ('mattress_type', 'TEXT')
    ]
    
    for col_name, col_type in furniture_cols:
        try:
            print(f"Adding {col_name} to furniture...")
            cursor.execute(f"ALTER TABLE furniture ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Already exists
            else:
                print(f"Error adding {col_name} to furniture: {e}")

    # 3. Upgrade other recommendation tables
    other_tables = ['user_activities', 'user_interests']
    for table in other_tables:
        try:
            print(f"Adding semantic_embedding to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN semantic_embedding TEXT")
        except sqlite3.OperationalError:
            pass
                 
    conn.commit()
    conn.close()
    print("Database migration complete.")

if __name__ == "__main__":
    upgrade_database()
