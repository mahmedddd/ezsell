import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('ezsell.db')
        cursor = conn.cursor()
        
        print("Starting migration: Adding fraud prevention columns to 'listings' table...")
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(listings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'listing_hash' not in columns:
            print("Adding column: listing_hash")
            cursor.execute("ALTER TABLE listings ADD COLUMN listing_hash TEXT")
            cursor.execute("CREATE INDEX idx_listings_hash ON listings(listing_hash)")
            
        if 'fraud_flags' not in columns:
            print("Adding column: fraud_flags")
            cursor.execute("ALTER TABLE listings ADD COLUMN fraud_flags TEXT")
            
        if 'rejection_reason' not in columns:
            print("Adding column: rejection_reason")
            cursor.execute("ALTER TABLE listings ADD COLUMN rejection_reason TEXT")
            
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
