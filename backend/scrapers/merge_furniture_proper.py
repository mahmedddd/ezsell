"""
Properly merge furniture datasets - FINAL VERSION
Strategy: Keep all unique entries from both datasets
"""

import pandas as pd
import numpy as np
import re

print("\n" + "="*80)
print("MERGING FURNITURE DATASETS - PROPER DEDUPLICATION")
print("="*80)

# Load both datasets
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

print(f"\n📂 Original: {len(orig)} rows")
print(f"📂 Scraped: {len(scraped)} rows")

# Standardize columns
orig.columns = [c.strip().title() for c in orig.columns]
scraped.columns = [c.strip().title() for c in scraped.columns]

# Rename Type to Category
if 'Type' in orig.columns:
    orig = orig.rename(columns={'Type': 'Category'})

# Target schema
target_columns = ['Title', 'Price', 'Category', 'Condition', 'Material', 'Description', 'URL']

for col in target_columns:
    if col not in orig.columns:
        orig[col] = ''
    if col not in scraped.columns:
        scraped[col] = ''

orig = orig[target_columns]
scraped = scraped[target_columns]

# Clean prices BEFORE concatenation
def clean_price(df):
    df['Price'] = df['Price'].astype(str).str.extract(r'(\d+)')[0]
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    # Multiply 3-digit prices by 100
    df['Price'] = df['Price'].apply(lambda x: x * 100 if (x >= 100 and x < 1000) else x)
    return df

print("\n💰 Cleaning prices...")
orig = clean_price(orig)
scraped = clean_price(scraped)

# Normalize text fields
def normalize_condition(val):
    if pd.isna(val) or val == '':
        return 'Used'
    val = str(val).strip().title()
    if val in ['New', 'Brand New']:
        return 'New'
    elif val in ['Excellent', 'Mint']:
        return 'Excellent'
    elif val in ['Good', 'Very Good']:
        return 'Good'
    elif val in ['Fair']:
        return 'Fair'
    return 'Used'

def normalize_material(val):
    if pd.isna(val) or val == '':
        return ''
    val = str(val).strip().title()
    if val in ['Wooden', 'Woods']:
        return 'Wood'
    elif val in ['Metallic', 'Steel']:
        return 'Metal'
    return val

def clean_category(val):
    if pd.isna(val) or val == '':
        return 'Furniture'
    val = str(val).strip().title()
    if 'Bed' in val:
        return 'Bed'
    elif 'Sofa' in val or 'Seater' in val:
        return 'Sofa'
    elif 'Table' in val or 'Desk' in val:
        return 'Table'
    elif 'Chair' in val:
        return 'Chair'
    elif 'Wardrobe' in val or 'Almari' in val:
        return 'Wardrobe'
    elif 'Cabinet' in val or 'Shelf' in val:
        return 'Cabinet'
    elif 'Dining' in val:
        return 'Dining'
    return 'Furniture'

print("🔧 Normalizing fields...")
for df in [orig, scraped]:
    df['Condition'] = df['Condition'].apply(normalize_condition)
    df['Material'] = df['Material'].apply(normalize_material)
    df['Category'] = df['Category'].apply(clean_category)

# Remove invalid rows BEFORE concatenation
print("\n🧹 Pre-cleaning datasets...")
orig = orig[orig['Price'].notnull()]
orig = orig[(orig['Price'] >= 1000) & (orig['Price'] <= 2000000)]
orig = orig[orig['Title'].str.len() > 5]
print(f"   Original after cleaning: {len(orig)} rows")

scraped = scraped[scraped['Price'].notnull()]
scraped = scraped[(scraped['Price'] >= 1000) & (scraped['Price'] <= 2000000)]
scraped = scraped[scraped['Title'].str.len() > 5]
print(f"   Scraped after cleaning: {len(scraped)} rows")

# Deduplicate WITHIN each dataset first
print("\n🔄 Deduplicating within datasets...")
orig = orig.drop_duplicates(subset=['URL'], keep='first')
scraped = scraped.drop_duplicates(subset=['URL'], keep='first')
print(f"   Original unique URLs: {len(orig)}")
print(f"   Scraped unique URLs: {len(scraped)}")

# Concatenate
print("\n🔗 Merging datasets...")
combined = pd.concat([orig, scraped], ignore_index=True)
print(f"   Total rows: {len(combined)}")

# Final deduplication - keep first occurrence (original takes precedence)
before_dedup = len(combined)
combined = combined.drop_duplicates(subset=['URL'], keep='first')
print(f"   Removed {before_dedup - len(combined)} duplicate URLs (overlap between datasets)")

# Secondary dedup by Title+Price (for cases with different/missing URLs)
before_dedup = len(combined)
combined = combined.drop_duplicates(subset=['Title', 'Price'], keep='first')
print(f"   Removed {before_dedup - len(combined)} duplicate Title+Price combinations")

# Reset index
combined = combined.reset_index(drop=True)

# Save
output_file = 'scraped_data/furniture_merged_final.csv'
combined.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n" + "="*80)
print("✅ MERGE COMPLETE!")
print("="*80)
print(f"📁 File: {output_file}")
print(f"📊 Total rows: {len(combined):,}")
print(f"💰 Price range: Rs.{combined['Price'].min():,.0f} - Rs.{combined['Price'].max():,.0f}")

# Summary
print("\n" + "="*80)
print("DATASET SUMMARY")
print("="*80)

print("\n📊 Category Distribution:")
for cat, count in combined['Category'].value_counts().head(10).items():
    print(f"   {cat}: {count:,}")

print("\n🔍 Condition Distribution:")
for cond, count in combined['Condition'].value_counts().items():
    print(f"   {cond}: {count:,}")

print("\n🪵 Top Materials:")
for mat, count in combined['Material'].value_counts().head(8).items():
    mat_name = mat if mat else '(Not specified)'
    print(f"   {mat_name}: {count:,}")

print("\n💰 Price Statistics:")
print(f"   Mean: Rs.{combined['Price'].mean():,.0f}")
print(f"   Median: Rs.{combined['Price'].median():,.0f}")
print(f"   Min: Rs.{combined['Price'].min():,.0f}")
print(f"   Max: Rs.{combined['Price'].max():,.0f}")

print("\n✅ Ready for ML training!")
