"""
Comprehensive analysis and merge of furniture datasets
"""

import pandas as pd
import numpy as np

print("="*80)
print("ANALYZING FURNITURE DATASETS")
print("="*80)

# Load both datasets
print("\n📂 Loading datasets...")
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

print(f"✅ Original furniture.csv: {len(orig)} rows")
print(f"✅ Scraped furniture_scraped: {len(scraped)} rows")

# Analyze structure
print("\n" + "="*80)
print("STRUCTURE ANALYSIS")
print("="*80)

print("\n📋 Original furniture.csv columns:")
print(f"   {list(orig.columns)}")
print("\n   Sample row:")
print(f"   {orig.iloc[0].to_dict()}")

print("\n📋 Scraped furniture_scraped columns:")
print(f"   {list(scraped.columns)}")
print("\n   Sample row:")
print(f"   {scraped.iloc[0].to_dict()}")

# Analyze prices
print("\n" + "="*80)
print("PRICE ANALYSIS")
print("="*80)

orig['Price_Numeric'] = pd.to_numeric(orig['Price'].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
scraped['Price_Numeric'] = pd.to_numeric(scraped['Price'].astype(str).str.extract(r'(\d+)')[0], errors='coerce')

print("\n💰 Original furniture.csv prices:")
print(f"   Range: {orig['Price_Numeric'].min():.0f} - {orig['Price_Numeric'].max():.0f}")
print(f"   3-digit prices (need *100): {len(orig[orig['Price_Numeric'] < 1000])} rows")
print(f"   Valid prices: {len(orig[orig['Price_Numeric'].notnull()])} rows")

print("\n💰 Scraped furniture prices:")
print(f"   Range: {scraped['Price_Numeric'].min():.0f} - {scraped['Price_Numeric'].max():.0f}")
print(f"   3-digit prices (need *100): {len(scraped[scraped['Price_Numeric'] < 1000])} rows")
print(f"   Valid prices: {len(scraped[scraped['Price_Numeric'].notnull()])} rows")

# Analyze categories/types
print("\n" + "="*80)
print("CATEGORY/TYPE ANALYSIS")
print("="*80)

print("\n📊 Original 'Type' column (top 10):")
if 'Type' in orig.columns:
    print(orig['Type'].value_counts().head(10))
else:
    print("   No 'Type' column found")

print("\n📊 Scraped 'Category' column (top 10):")
if 'Category' in scraped.columns:
    print(scraped['Category'].value_counts().head(10))
else:
    print("   No 'Category' column found")

# Analyze conditions
print("\n" + "="*80)
print("CONDITION ANALYSIS")
print("="*80)

print("\n🔍 Original 'Condition' values:")
print(orig['Condition'].value_counts())

print("\n🔍 Scraped 'Condition' values:")
print(scraped['Condition'].value_counts())

# Analyze materials
print("\n" + "="*80)
print("MATERIAL ANALYSIS")
print("="*80)

print("\n🪵 Original 'Material' values (top 10):")
print(orig['Material'].value_counts().head(10))

print("\n🪵 Scraped 'Material' values (top 10):")
print(scraped['Material'].value_counts().head(10))

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
