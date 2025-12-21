"""
Merge furniture datasets - KEEP ALL UNIQUE URLs (no Title+Price dedup)
"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("FURNITURE MERGE - MAXIMUM DATA RETENTION")
print("="*80)

# Load
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

print(f"\n📂 Original: {len(orig)} rows")
print(f"📂 Scraped: {len(scraped)} rows (with {len(scraped) - scraped['URL'].nunique()} duplicates)")

# Standardize
orig.columns = [c.strip() for c in orig.columns]
scraped.columns = [c.strip() for c in scraped.columns]

if 'Type' in orig.columns:
    orig = orig.rename(columns={'Type': 'Category'})

cols = ['Title', 'Price', 'Category', 'Condition', 'Material', 'Description', 'URL']
for col in cols:
    if col not in orig.columns:
        orig[col] = ''
    if col not in scraped.columns:
        scraped[col] = ''

orig = orig[cols]
scraped = scraped[cols]

# Clean prices
def fix_price(p):
    if pd.isna(p):
        return np.nan
    p = str(p).replace(',', '')
    try:
        p = float(p)
        if 100 <= p < 1000:
            p = p * 100
        return p
    except:
        return np.nan

orig['Price'] = orig['Price'].apply(fix_price)
scraped['Price'] = scraped['Price'].apply(fix_price)

# Normalize
def norm_cond(c):
    if pd.isna(c) or c == '':
        return 'Used'
    c = str(c).title()
    if c in ['New', 'Brand New']:
        return 'New'
    elif c in ['Excellent', 'Mint']:
        return 'Excellent'
    elif c == 'Good':
        return 'Good'
    elif c == 'Fair':
        return 'Fair'
    return 'Used'

def norm_mat(m):
    if pd.isna(m) or m == '':
        return ''
    m = str(m).title().strip()
    if m in ['Wooden', 'Woods']:
        return 'Wood'
    elif m in ['Metallic', 'Steel']:
        return 'Metal'
    return m

def norm_cat(c):
    if pd.isna(c) or c == '':
        return 'Furniture'
    c = str(c).title()
    if 'Bed' in c:
        return 'Bed'
    elif 'Sofa' in c or 'Seater' in c:
        return 'Sofa'
    elif 'Table' in c or 'Desk' in c:
        return 'Table'
    elif 'Chair' in c:
        return 'Chair'
    elif 'Wardrobe' in c or 'Almari' in c:
        return 'Wardrobe'
    elif 'Cabinet' in c or 'Shelf' in c:
        return 'Cabinet'
    elif 'Dining' in c:
        return 'Dining'
    return 'Furniture'

orig['Condition'] = orig['Condition'].apply(norm_cond)
orig['Material'] = orig['Material'].apply(norm_mat)
orig['Category'] = orig['Category'].apply(norm_cat)

scraped['Condition'] = scraped['Condition'].apply(norm_cond)
scraped['Material'] = scraped['Material'].apply(norm_mat)
scraped['Category'] = scraped['Category'].apply(norm_cat)

# Concatenate
combined = pd.concat([orig, scraped], ignore_index=True)
print(f"\n🔗 Combined: {len(combined)} rows")

# Filter
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 1000) & (combined['Price'] <= 2000000)]
combined = combined[combined['Title'].str.len() > 5]
print(f"🧹 After filtering: {len(combined)} rows")

# ONLY deduplicate by URL (keep all unique items)
combined = combined.drop_duplicates(subset=['URL'], keep='first')
print(f"✂️  After URL dedup: {len(combined)} rows")

# Save
combined = combined.reset_index(drop=True)
output = 'scraped_data/furniture_merged_all.csv'
combined.to_csv(output, index=False, encoding='utf-8-sig')

print("\n" + "="*80)
print("✅ MERGED - MAXIMUM DATA RETENTION")
print("="*80)
print(f"📁 {output}")
print(f"📊 Total Rows: {len(combined):,}")
print(f"💰 Price Range: Rs.{combined['Price'].min():,.0f} - Rs.{combined['Price'].max():,.0f}")

print("\n📊 Categories:")
print(combined['Category'].value_counts().head(8))

print("\n🔍 Conditions:")
print(combined['Condition'].value_counts())

print("\n🪵 Materials:")
mat_counts = combined['Material'].value_counts().head(8)
for mat, count in mat_counts.items():
    mat_name = mat if mat else '(Not specified)'
    print(f"  {mat_name}: {count}")

print(f"\n✅ Dataset ready for ML with {len(combined):,} unique furniture items!")
