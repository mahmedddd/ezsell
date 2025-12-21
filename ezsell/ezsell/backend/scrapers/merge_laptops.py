"""
Merge laptop datasets - Maximum data retention
"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("LAPTOP DATASET MERGE")
print("="*80)

# Load both datasets
orig = pd.read_csv(r'../../laptops.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/laptop_scraped_20251221_051440.csv', on_bad_lines='skip')

print(f"\n📂 Original laptops.csv: {len(orig)} rows")
print(f"📂 Scraped laptop_scraped: {len(scraped)} rows")

# Standardize column names
orig.columns = [c.strip() for c in orig.columns]
scraped.columns = [c.strip() for c in scraped.columns]

print(f"\nOriginal columns: {list(orig.columns)}")
print(f"Scraped columns: {list(scraped.columns)}")

# Target columns (use original schema)
cols = ['Title', 'Price', 'Brand', 'Model', 'Condition', 'Type', 'Description', 'URL']

# Add missing columns
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
        # Multiply 3-digit prices by 100
        if 100 <= p < 1000:
            p = p * 100
        return p
    except:
        return np.nan

orig['Price'] = orig['Price'].apply(fix_price)
scraped['Price'] = scraped['Price'].apply(fix_price)

# Normalize condition
def norm_cond(c):
    if pd.isna(c) or c == '':
        return 'Used'
    c = str(c).title().strip()
    if c in ['New', 'Brand New', 'Fresh']:
        return 'New'
    elif c in ['Excellent', 'Mint', 'Like New']:
        return 'Excellent'
    elif c == 'Good':
        return 'Good'
    elif c == 'Fair':
        return 'Fair'
    return 'Used'

orig['Condition'] = orig['Condition'].apply(norm_cond)
scraped['Condition'] = scraped['Condition'].apply(norm_cond)

# Normalize brand
def norm_brand(b):
    if pd.isna(b) or b == '':
        return ''
    b = str(b).title().strip()
    # Standardize common variations
    if b in ['Hp', 'Hewlett-Packard']:
        return 'HP'
    elif b in ['Lenovo']:
        return 'Lenovo'
    elif b in ['Dell']:
        return 'Dell'
    elif b in ['Apple']:
        return 'Apple'
    elif b in ['Asus']:
        return 'ASUS'
    elif b in ['Acer']:
        return 'Acer'
    elif b in ['Msi', 'Micro-Star']:
        return 'MSI'
    return b

orig['Brand'] = orig['Brand'].apply(norm_brand)
scraped['Brand'] = scraped['Brand'].apply(norm_brand)

# Normalize type/category
def norm_type(t):
    if pd.isna(t) or t == '':
        return 'Laptop'
    t = str(t).title().strip()
    if 'Gaming' in t:
        return 'Gaming'
    elif 'Business' in t or 'Traditional' in t:
        return 'Business'
    elif 'Ultrabook' in t:
        return 'Ultrabook'
    elif 'MacBook' in t or 'Macbook' in t:
        return 'MacBook'
    elif 'Chrome' in t:
        return 'Chromebook'
    return 'Laptop'

orig['Type'] = orig['Type'].apply(norm_type)
scraped['Type'] = scraped['Type'].apply(norm_type)

# Concatenate
combined = pd.concat([orig, scraped], ignore_index=True)
print(f"\n🔗 Combined: {len(combined)} rows")

# Filter valid data
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 5000) & (combined['Price'] <= 2000000)]
combined = combined[combined['Title'].str.len() > 5]
print(f"🧹 After filtering: {len(combined)} rows")

# Check URL statistics
print(f"\n📊 URL Analysis:")
print(f"   Unique URLs: {combined['URL'].nunique()}")
print(f"   Duplicate URLs: {len(combined) - combined['URL'].nunique()}")

# Deduplicate by URL only (keep all unique laptops)
combined = combined.drop_duplicates(subset=['URL'], keep='first')
print(f"✂️  After URL dedup: {len(combined)} rows")

# Save
combined = combined.reset_index(drop=True)
output = 'scraped_data/laptop_merged_all.csv'
combined.to_csv(output, index=False, encoding='utf-8-sig')

print("\n" + "="*80)
print("✅ LAPTOP MERGE COMPLETE!")
print("="*80)
print(f"📁 File: {output}")
print(f"📊 Total Rows: {len(combined):,}")
print(f"💰 Price Range: Rs.{combined['Price'].min():,.0f} - Rs.{combined['Price'].max():,.0f}")

print("\n📊 Brand Distribution:")
print(combined['Brand'].value_counts().head(10))

print("\n🔍 Condition Distribution:")
print(combined['Condition'].value_counts())

print("\n💻 Type Distribution:")
print(combined['Type'].value_counts())

print(f"\n✅ Dataset ready for ML with {len(combined):,} unique laptops!")
