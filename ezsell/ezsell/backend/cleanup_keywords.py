
import sqlite3
import json
import os
from core.nlp_service import KeywordExtractor

def cleanup_legacy_keywords():
    db_path = 'ezsell.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, keywords FROM user_activities WHERE keywords IS NOT NULL')
    rows = cursor.fetchall()
    
    updated_count = 0
    for row_id, keywords_json in rows:
        try:
            keywords = json.loads(keywords_json)
            # Apply the current filtering logic
            cleaned_kws = [
                kw for kw in keywords 
                if kw.lower() not in KeywordExtractor.STOPWORDS 
                and not any(word in KeywordExtractor.STOPWORDS for word in kw.lower().split())
            ]
            
            if len(cleaned_kws) != len(keywords):
                new_keywords_json = json.dumps(cleaned_kws)
                cursor.execute('UPDATE user_activities SET keywords = ? WHERE id = ?', (new_keywords_json, row_id))
                updated_count += 1
        except json.JSONDecodeError:
            continue
            
    conn.commit()
    print(f"Cleaned up {updated_count} activities with legacy junk keywords.")

if __name__ == "__main__":
    cleanup_legacy_keywords()
