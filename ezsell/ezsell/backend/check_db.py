import sqlite3
conn = sqlite3.connect('ezsell.db')
cur = conn.cursor()
# Check furniture listings
cur.execute("SELECT id, title, description, furniture_type, furniture_subtype, material FROM listings WHERE category='furniture'")
rows = cur.fetchall()
print(f"Furniture listings ({len(rows)} total):")
for r in rows:
    print(f"  id={r[0]} type={r[3]} subtype={r[4]} material={r[5]} title={r[1]!r}")
# Also check PRAGMA table_info to confirm column exists
cur.execute("PRAGMA table_info(listings)")
cols = [c[1] for c in cur.fetchall()]
print(f"\nListings columns: {cols}")
print(f"\nfurniture_subtype in schema: {'furniture_subtype' in cols}")
conn.close()
