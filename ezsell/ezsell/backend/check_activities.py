
import sqlite3
import json
import os

def check_bed_activities():
    db_path = 'ezsell.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Searches for 'bed' ---")
    cursor.execute('SELECT id, activity_type, search_query, keywords, created_at FROM user_activities WHERE search_query LIKE "%bed%" ORDER BY created_at DESC LIMIT 10')
    cols = [d[0] for d in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    print(json.dumps(rows, indent=2))

    print("\n--- Recent Activities with 'bed' in Keywords ---")
    cursor.execute('SELECT id, activity_type, search_query, keywords, created_at FROM user_activities WHERE keywords LIKE "%bed%" ORDER BY created_at DESC LIMIT 10')
    cols = [d[0] for d in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    print(json.dumps(rows, indent=2))

if __name__ == "__main__":
    check_bed_activities()
