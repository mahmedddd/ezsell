import sqlite3
conn = sqlite3.connect('ezsell.db')
cur = conn.cursor()
cur.execute("SELECT id, title, furniture_type, furniture_subtype FROM listings WHERE furniture_type='wardrobe' OR title LIKE '%wardrobe%' OR title LIKE '%Wardrobe%'")
rows = cur.fetchall()
print('Found wardrobe listings:', rows)
updated = 0
for row in rows:
    lid, title, ftype, fsubtype = row
    if not fsubtype:
        conn.execute("UPDATE listings SET furniture_subtype='3_door' WHERE id=?", (lid,))
        print(f'Updated listing id={lid} title="{title}" -> furniture_subtype=3_door')
        updated += 1
    else:
        print(f'Listing id={lid} already has subtype={fsubtype}')
conn.commit()
conn.close()
print(f'Done. Updated {updated} listing(s).')
