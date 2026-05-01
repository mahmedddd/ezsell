
import sqlite3

def list_all_columns():
    conn = sqlite3.connect('ezsell.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(listings)")
    cols = cursor.fetchall()
    column_names = [col[1] for col in cols]
    print(f"All columns in 'listings': {column_names}")
    
    if 'is_active' not in column_names:
        print("'is_active' column is MISSING! Adding it now...")
        cursor.execute("ALTER TABLE listings ADD COLUMN is_active BOOLEAN DEFAULT 1")
        conn.commit()
        print("Column 'is_active' added successfully.")
    else:
        print("'is_active' column ALREADY EXISTS.")
        
    conn.close()

if __name__ == "__main__":
    list_all_columns()
