"""
Merge mobile datasets - Combining extensive scraped data with cleaned dataset
"""

import pandas as pd
import numpy as np
import re

print("\n" + "="*80)
print("MOBILE DATASET MERGE")
print("="*80)

# Load both datasets
scraped = pd.read_csv(r'scraped_data/mobile_scraped_20251221_034552.csv', on_bad_lines='skip')
cleaned = pd.read_csv(r'../../cleaned_mobiles.csv', on_bad_lines='skip')

print(f"\n📂 Scraped mobiles: {len(scraped)} rows")
print(f"📂 Cleaned mobiles: {len(cleaned)} rows")

# Standardize column names
scraped.columns = [c.strip() for c in scraped.columns]
cleaned.columns = [c.strip() for c in cleaned.columns]

print(f"\nScraped columns: {list(scraped.columns)}")
print(f"Cleaned columns: {list(cleaned.columns)}")

# Use scraped dataset columns as base (more extensive)
target_cols = ['Title', 'Price', 'Brand', 'Condition', 'Location', 'Description', 
               'URL', 'Scraped_Date', 'RAM', 'Storage', 'Camera_MP', 'Battery_mAh', 
               'Screen_Size', 'Is_5G', 'PTA_Approved', 'Has_Warranty', 'Has_Box']

# Add missing columns to cleaned dataset
for col in target_cols:
    if col not in cleaned.columns:
        if col in ['RAM', 'Storage', 'Camera_MP', 'Battery_mAh', 'Screen_Size']:
            cleaned[col] = np.nan
        elif col in ['Is_5G', 'PTA_Approved', 'Has_Warranty', 'Has_Box']:
            cleaned[col] = 0
        else:
            cleaned[col] = ''

# Ensure scraped has all columns
for col in target_cols:
    if col not in scraped.columns:
        scraped[col] = ''

# Reorder columns
scraped = scraped[target_cols]
cleaned = cleaned[target_cols]

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

scraped['Price'] = scraped['Price'].apply(fix_price)
cleaned['Price'] = cleaned['Price'].apply(fix_price)

# Normalize brand names
def norm_brand(b):
    if pd.isna(b) or b == '':
        return ''
    b = str(b).title().strip()
    
    # Apple variations
    if 'Apple' in b or 'Iphone' in b or 'IPhone' in b:
        return 'Apple'
    # Samsung
    elif 'Samsung' in b:
        return 'Samsung'
    # OPPO
    elif b.upper() in ['OPPO']:
        return 'OPPO'
    # Vivo
    elif b in ['Vivo']:
        return 'Vivo'
    # Infinix
    elif b in ['Infinix']:
        return 'Infinix'
    # Tecno
    elif b in ['Tecno', 'Techno']:
        return 'Tecno'
    # Huawei/Honor
    elif b in ['Huawei', 'Hawaii']:
        return 'Huawei'
    elif b in ['Honor']:
        return 'Honor'
    # Google
    elif b in ['Google']:
        return 'Google'
    # OnePlus
    elif 'Oneplus' in b or 'One Plus' in b:
        return 'OnePlus'
    # Realme
    elif b in ['Realme']:
        return 'Realme'
    # Xiaomi/Redmi
    elif b in ['Xiaomi', 'Redmi']:
        return 'Xiaomi'
    # Nokia
    elif b in ['Nokia']:
        return 'Nokia'
    # Motorola
    elif b in ['Motorola', 'Moto']:
        return 'Motorola'
    # Itel
    elif b in ['Itel']:
        return 'Itel'
    # Sony
    elif b in ['Sony']:
        return 'Sony'
    elif b in ['Other Mobiles']:
        return 'Others'
    return b

scraped['Brand'] = scraped['Brand'].apply(norm_brand)
cleaned['Brand'] = cleaned['Brand'].apply(norm_brand)

# Normalize condition
def norm_cond(c):
    if pd.isna(c) or c == '':
        return 'Used'
    c = str(c).title().strip()
    if c in ['New', 'Brand New', 'Fresh']:
        return 'New'
    elif c in ['Open Box', 'Openbox']:
        return 'Open Box'
    elif c in ['Refurbished']:
        return 'Refurbished'
    elif c in ['For Parts Or Not Working', 'For Parts', 'Not Working']:
        return 'For Parts'
    return 'Used'

scraped['Condition'] = scraped['Condition'].apply(norm_cond)
cleaned['Condition'] = cleaned['Condition'].apply(norm_cond)

# Extract RAM and Storage from Title for cleaned dataset
def extract_ram_storage(title):
    """Extract RAM/Storage from title like '8/128' or '8gb/256gb'"""
    if pd.isna(title):
        return None, None
    
    title_str = str(title).lower()
    
    # Pattern: 8/128, 8gb/256gb, etc.
    match = re.search(r'(\d+)\s*gb?\s*/\s*(\d+)\s*gb?', title_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Pattern: 8gb ram 128gb
    ram_match = re.search(r'(\d+)\s*gb\s*ram', title_str)
    storage_match = re.search(r'(\d+)\s*gb(?!\s*ram)', title_str)
    
    ram = int(ram_match.group(1)) if ram_match else None
    storage = int(storage_match.group(1)) if storage_match else None
    
    return ram, storage

# Fill missing RAM/Storage for cleaned dataset
for idx, row in cleaned.iterrows():
    if pd.isna(row['RAM']) or pd.isna(row['Storage']):
        ram, storage = extract_ram_storage(row['Title'])
        if ram:
            cleaned.at[idx, 'RAM'] = ram
        if storage:
            cleaned.at[idx, 'Storage'] = storage

# Concatenate
combined = pd.concat([scraped, cleaned], ignore_index=True)
print(f"\n🔗 Combined: {len(combined)} rows")

# Filter valid data
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 1000) & (combined['Price'] <= 1000000)]
combined = combined[combined['Title'].str.len() > 5]
print(f"🧹 After filtering: {len(combined)} rows")

# Check URL statistics
print(f"\n📊 URL Analysis:")
print(f"   Unique URLs: {combined['URL'].nunique()}")
print(f"   Duplicate URLs: {len(combined) - combined['URL'].nunique()}")

# Deduplicate by URL only (keep first occurrence with most data)
# Sort by number of non-null values to keep richer records
combined['data_completeness'] = combined.notna().sum(axis=1)
combined = combined.sort_values('data_completeness', ascending=False)
combined = combined.drop_duplicates(subset=['URL'], keep='first')
combined = combined.drop('data_completeness', axis=1)
print(f"✂️  After URL dedup: {len(combined)} rows")

# Save
combined = combined.reset_index(drop=True)
output = 'scraped_data/mobile_merged_all.csv'
combined.to_csv(output, index=False, encoding='utf-8-sig')

print("\n" + "="*80)
print("✅ MOBILE MERGE COMPLETE!")
print("="*80)
print(f"📁 File: {output}")
print(f"📊 Total Rows: {len(combined):,}")
print(f"💰 Price Range: Rs.{combined['Price'].min():,.0f} - Rs.{combined['Price'].max():,.0f}")

print("\n📱 Brand Distribution:")
print(combined['Brand'].value_counts().head(15))

print("\n🔍 Condition Distribution:")
print(combined['Condition'].value_counts())

print("\n📊 Feature Completeness:")
print(f"   RAM data: {combined['RAM'].notna().sum()} ({100*combined['RAM'].notna().sum()/len(combined):.1f}%)")
print(f"   Storage data: {combined['Storage'].notna().sum()} ({100*combined['Storage'].notna().sum()/len(combined):.1f}%)")
print(f"   Camera data: {combined['Camera_MP'].notna().sum()} ({100*combined['Camera_MP'].notna().sum()/len(combined):.1f}%)")
print(f"   PTA Approved: {combined['PTA_Approved'].sum()} phones")
print(f"   5G Capable: {combined['Is_5G'].sum()} phones")
print(f"   Has Box: {combined['Has_Box'].sum()} phones")

print(f"\n✅ Dataset ready for ML with {len(combined):,} unique mobiles!")
print(f"🎯 Rich feature set for better price prediction accuracy!")
