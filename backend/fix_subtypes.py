"""
Generic furniture_subtype inference fix.
Updates ALL furniture listings that have a NULL furniture_subtype by
analysing the listing title + description with the same keyword rules
used by the frontend (resolveSmartDimensions / parseDoorCount).
"""

import sqlite3
import re

# ─── Subtype inference rules per furniture_type ────────────────────────────────

def infer_wardrobe(text: str) -> str:
    if re.search(r'6[\s-]*door|six[\s-]*door', text):   return '6_door'
    if re.search(r'5[\s-]*door|five[\s-]*door', text):   return '5_door'
    if re.search(r'4[\s-]*door|four[\s-]*door', text):   return '4_door'
    if re.search(r'3[\s-]*door|three[\s-]*door', text):  return '3_door'
    if re.search(r'2[\s-]*door|two[\s-]*door', text):    return '2_door'
    if re.search(r'sliding', text):                       return 'sliding'
    if re.search(r'walk[\s-]*in', text):                  return 'walk_in'
    return '2_door'  # safest default

def infer_sofa(text: str) -> str:
    if re.search(r'7[\s-]*seater|seven[\s-]*seater', text):   return '7_seater'
    if re.search(r'6[\s-]*seater|six[\s-]*seater', text):     return '6_seater'
    if re.search(r'5[\s-]*seater|five[\s-]*seater', text):    return '5_seater'
    if re.search(r'4[\s-]*seater|four[\s-]*seater', text):    return '4_seater'
    if re.search(r'3[\s-]*seater|three[\s-]*seater', text):   return '3_seater'
    if re.search(r'2[\s-]*seater|two[\s-]*seater|loveseat', text): return '2_seater'
    if re.search(r'1[\s-]*seater|single[\s-]*seater', text):  return '1_seater'
    if re.search(r'l[\s-]*shaped|sectional', text):            return 'l_shaped'
    if re.search(r'sofa.{0,10}bed|sofa.{0,10}cum|cum.{0,10}bed', text): return 'sofa_cum_bed'
    if re.search(r'recliner', text):                           return 'recliner'
    return '3_seater'  # default

def infer_bed(text: str) -> str:
    if re.search(r'king[\s-]*size|king[\s-]*bed|\bking\b', text):     return 'king'
    if re.search(r'queen[\s-]*size|queen[\s-]*bed|\bqueen\b', text):  return 'queen'
    if re.search(r'double[\s-]*bed|full[\s-]*size|\bdouble\b', text): return 'double'
    if re.search(r'bunk[\s-]*bed|\bbunk\b', text):                    return 'bunk'
    if re.search(r'single[\s-]*bed|twin[\s-]*bed|\bsingle\b|\btwin\b', text): return 'single'
    return 'double'

def infer_table(text: str) -> str:
    if re.search(r'10[\s-]*seater|ten[\s-]*person', text):   return 'dining_8'  # closest
    if re.search(r'8[\s-]*seater|eight[\s-]*person', text):  return 'dining_8'
    if re.search(r'6[\s-]*seater|six[\s-]*person', text):    return 'dining_6'
    if re.search(r'4[\s-]*seater|four[\s-]*person', text):   return 'dining_4'
    if re.search(r'2[\s-]*seater|two[\s-]*person', text):    return 'dining_4'
    if re.search(r'coffee', text):                            return 'coffee'
    if re.search(r'side[\s-]*table|end[\s-]*table', text):   return 'side'
    if re.search(r'console', text):                           return 'console'
    if re.search(r'study|writing', text):                     return 'study'
    if re.search(r'dining', text):                            return 'dining_4'
    return 'dining_4'

def infer_chair(text: str) -> str:
    if re.search(r'gaming[\s-]*chair', text):    return 'gaming'
    if re.search(r'office[\s-]*chair|revolving|executive[\s-]*chair', text): return 'office'
    if re.search(r'rocking[\s-]*chair|\brocking\b', text): return 'rocking'
    if re.search(r'dining[\s-]*chair|\bdining\b', text): return 'dining'
    if re.search(r'accent', text):               return 'accent'
    if re.search(r'bean[\s-]*bag', text):        return 'bean_bag'
    return 'dining'

def infer_desk(text: str) -> str:
    if re.search(r'l[\s-]*shaped', text):         return 'l_shaped'
    if re.search(r'standing[\s-]*desk|stand[\s-]*up', text): return 'standing'
    if re.search(r'executive', text):             return 'executive'
    if re.search(r'computer[\s-]*desk|pc[\s-]*desk', text): return 'computer'
    if re.search(r'writing[\s-]*desk|writing', text): return 'writing'
    if re.search(r'study[\s-]*desk|study', text): return 'writing'
    return 'computer'

def infer_cabinet(text: str) -> str:
    if re.search(r'kitchen[\s-]*cabinet', text):  return 'kitchen'
    if re.search(r'bathroom|washroom', text):      return 'bathroom'
    if re.search(r'display[\s-]*cabinet|china[\s-]*cabinet|showcase', text): return 'display'
    if re.search(r'filing[\s-]*cabinet|file[\s-]*cabinet', text): return 'filing'
    return 'storage'

def infer_bookshelf(text: str) -> str:
    if re.search(r'wall[\s-]*shelf|floating[\s-]*shelf', text): return 'wall_shelf'
    if re.search(r'corner[\s-]*shelf', text):     return 'corner'
    if re.search(r'shoe[\s-]*rack|shoes?\s+rack', text): return 'shoe_rack'
    if re.search(r'\bshelf\b|bookshelf|bookcase', text): return 'bookshelf'
    return 'bookshelf'

def infer_dresser(text: str) -> str:
    if re.search(r'vanity', text):    return 'vanity'
    if re.search(r'mirror', text):    return 'with_mirror'
    if re.search(r'storage|drawer', text): return 'with_storage'
    return 'simple'

def infer_ottoman(text: str) -> str:
    if re.search(r'round|circular|pouf', text): return 'round'
    if re.search(r'storage', text):              return 'storage'
    return 'rectangular'

INFERRERS = {
    'wardrobe':       infer_wardrobe,
    'sofa':           infer_sofa,
    'couch':          infer_sofa,
    'bed':            infer_bed,
    'table':          infer_table,
    'dining_table':   infer_table,
    'coffee_table':   lambda t: 'coffee',
    'chair':          infer_chair,
    'office_chair':   lambda t: 'office',
    'dining_chair':   lambda t: 'dining',
    'desk':           infer_desk,
    'cabinet':        infer_cabinet,
    'bookshelf':      infer_bookshelf,
    'shelf':          infer_bookshelf,
    'dresser':        infer_dresser,
    'dressing_table': infer_dresser,
    'ottoman':        infer_ottoman,
}

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect('ezsell.db')
    cur = conn.cursor()

    # Get ALL furniture listings missing a subtype
    cur.execute("""
        SELECT id, title, description, furniture_type, furniture_subtype
        FROM listings
        WHERE furniture_type IS NOT NULL
          AND (furniture_subtype IS NULL OR furniture_subtype = '')
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} furniture listing(s) with missing subtype.\n")

    updated = 0
    for lid, title, desc, ftype, _ in rows:
        ftype_key = (ftype or '').lower().strip()
        text = f"{title or ''} {desc or ''}".lower()

        inferrer = INFERRERS.get(ftype_key)
        if inferrer:
            subtype = inferrer(text)
        else:
            subtype = None  # unknown furniture type — leave as NULL

        if subtype:
            conn.execute(
                "UPDATE listings SET furniture_subtype=? WHERE id=?",
                (subtype, lid)
            )
            print(f"  id={lid:>4}  type={ftype_key:<16}  title={title!r:<40}  → {subtype}")
            updated += 1
        else:
            print(f"  id={lid:>4}  type={ftype_key:<16}  SKIPPED (no inferrer)")

    conn.commit()
    conn.close()
    print(f"\nDone. Updated {updated} of {len(rows)} listing(s).")

if __name__ == '__main__':
    main()
