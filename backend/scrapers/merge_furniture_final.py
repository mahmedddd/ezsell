"""
Properly merge both furniture datasets with comprehensive cleaning
Based on structure analysis:
- Original: Title, Price, Description, Condition, Type, Material, URL (1072 rows)
- Scraped: Title, Price, Category, Condition, Material, Description, URL (2692 rows)
"""

import pandas as pd
import numpy as np
import re

print("\n" + "="*80)
print("MERGING FURNITURE DATASETS")
print("="*80)

# Load both datasets
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

print(f"\n📂 Loaded original: {len(orig)} rows")
print(f"📂 Loaded scraped: {len(scraped)} rows")

# Standardize column names
orig.columns = [c.strip().title() for c in orig.columns]
scraped.columns = [c.strip().title() for c in scraped.columns]

# Rename 'Type' to 'Category' in original to match scraped
if 'Type' in orig.columns:
    orig = orig.rename(columns={'Type': 'Category'})

# Ensure both have same columns in same order
target_columns = ['Title', 'Price', 'Category', 'Condition', 'Material', 'Description', 'URL']

# Add missing columns with empty values
for col in target_columns:
    if col not in orig.columns:
        orig[col] = ''
    if col not in scraped.columns:
        scraped[col] = ''

# Select columns in correct order
orig = orig[target_columns]
scraped = scraped[target_columns]

print(f"\n✅ Aligned columns: {target_columns}")

# Clean and normalize prices
def clean_price(df):
    # Extract numeric price
    df['Price'] = df['Price'].astype(str).str.extract(r'(\d+)')[0]
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    
    # Multiply 3-digit prices by 100 (e.g., 243 -> 24300)
    df['Price'] = df['Price'].apply(lambda x: x * 100 if (x >= 100 and x < 1000) else x)
    
    return df

print("\n💰 Cleaning prices...")
orig = clean_price(orig)
scraped = clean_price(scraped)

print(f"   Original: {len(orig[orig['Price'].notnull()])} valid prices")
print(f"   Scraped: {len(scraped[scraped['Price'].notnull()])} valid prices")

# Normalize condition values
def normalize_condition(val):
    if pd.isna(val) or val == '':
        return 'Used'
    val = str(val).strip().title()
    # Map variations
    if val in ['New', 'Brand New', 'Fresh']:
        return 'New'
    elif val in ['Excellent', 'Mint', 'Like New']:
        return 'Excellent'
    elif val in ['Good', 'Very Good']:
        return 'Good'
    elif val in ['Fair', 'Average']:
        return 'Fair'
    else:
        return 'Used'

print("\n🔧 Normalizing conditions...")
orig['Condition'] = orig['Condition'].apply(normalize_condition)
scraped['Condition'] = scraped['Condition'].apply(normalize_condition)

# Normalize material values
def normalize_material(val):
    if pd.isna(val) or val == '':
        return ''
    val = str(val).strip().title()
    # Standardize common variations
    if val in ['Wooden', 'Woods']:
        return 'Wood'
    elif val in ['Metallic', 'Steel', 'Stainless']:
        return 'Metal'
    return val

print("🪵 Normalizing materials...")
orig['Material'] = orig['Material'].apply(normalize_material)
scraped['Material'] = scraped['Material'].apply(normalize_material)

# Clean category values
def clean_category(val):
    if pd.isna(val) or val == '':
        return 'Furniture'
    val = str(val).strip().title()
    # Standardize
    if 'Bed' in val:
        return 'Bed'
    elif 'Sofa' in val or 'Seater' in val:
        return 'Sofa'
    elif 'Table' in val or 'Desk' in val:
        return 'Table'
    elif 'Chair' in val:
        return 'Chair'
    elif 'Wardrobe' in val or 'Almari' in val or 'Almirah' in val:
        return 'Wardrobe'
    elif 'Cabinet' in val or 'Shelf' in val:
        return 'Cabinet'
    elif 'Dining' in val:
        return 'Dining'
    else:
        return 'Furniture'

print("📊 Normalizing categories...")
orig['Category'] = orig['Category'].apply(clean_category)
scraped['Category'] = scraped['Category'].apply(clean_category)

# Concatenate datasets
print("\n🔗 Concatenating datasets...")
combined = pd.concat([orig, scraped], ignore_index=True)
print(f"   Total before cleaning: {len(combined)} rows")

# Remove rows with invalid prices
print("\n🧹 Cleaning data...")
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 1000) & (combined['Price'] <= 2000000)]
print(f"   After price filter: {len(combined)} rows")

# Remove rows with empty or short titles
combined = combined[combined['Title'].str.len() > 5]
print(f"   After title filter: {len(combined)} rows")

# Deduplicate intelligently
# First, mark which rows have better data (more complete)
combined['completeness_score'] = (
    combined['Title'].str.len().fillna(0) +
    combined['Description'].str.len().fillna(0) +
    (~combined['Material'].isna()).astype(int) * 50 +
    (~combined['Category'].isna()).astype(int) * 50
)

# Sort by completeness (keep best rows)
combined = combined.sort_values('completeness_score', ascending=False)

# Remove duplicates by URL (keep most complete)
before_dedup = len(combined)
combined = combined.drop_duplicates(subset=['URL'], keep='first')
print(f"   Removed {before_dedup - len(combined)} duplicate URLs")

# Only deduplicate by Title+Price if URL is missing/invalid
before_dedup = len(combined)
combined = combined.drop_duplicates(subset=['Title', 'Price'], keep='first')
print(f"   Removed {before_dedup - len(combined)} duplicate Title+Price")

# Drop the temporary score column
combined = combined.drop(columns=['completeness_score'])

# Reset index
combined = combined.reset_index(drop=True)

# Save merged dataset
output_file = 'scraped_data/furniture_merged_final.csv'
combined.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n" + "="*80)
print("✅ MERGE COMPLETE!")
print("="*80)
print(f"📁 Saved to: {output_file}")
print(f"📊 Total rows: {len(combined):,}")
print(f"💰 Price range: Rs.{combined['Price'].min():,.0f} - Rs.{combined['Price'].max():,.0f}")

# Summary statistics
print("\n" + "="*80)
print("MERGED DATASET SUMMARY")
print("="*80)

print("\n📊 Category Distribution:")
for cat, count in combined['Category'].value_counts().head(10).items():
    print(f"   {cat}: {count}")

print("\n🔍 Condition Distribution:")
for cond, count in combined['Condition'].value_counts().items():
    print(f"   {cond}: {count}")

print("\n🪵 Material Distribution (top 10):")
for mat, count in combined['Material'].value_counts().head(10).items():
    mat_name = mat if mat else '(Not specified)'
    print(f"   {mat_name}: {count}")

print("\n💰 Price Statistics:")
print(f"   Mean: Rs.{combined['Price'].mean():,.0f}")
print(f"   Median: Rs.{combined['Price'].median():,.0f}")
print(f"   Std Dev: Rs.{combined['Price'].std():,.0f}")

print("\n✅ Dataset is ready for price prediction training!")
