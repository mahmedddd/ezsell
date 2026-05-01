"""
Combine original and scraped furniture datasets for price prediction
- Deduplicate by URL and Title+Price
- Remove rows with missing or invalid price
- Normalize columns for ML
- Save as furniture_combined_ready.csv
"""

import pandas as pd
import numpy as np
import re

# Load both datasets
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

# Standardize column names (strip, lower, title-case)
def clean_cols(df):
    df.columns = [c.strip().title() for c in df.columns]
    return df

orig = clean_cols(orig)
scraped = clean_cols(scraped)

# Ensure all required columns exist
all_cols = ['Title','Price','Category','Condition','Material','Description','URL']
for col in all_cols:
    if col not in orig.columns:
        orig[col] = ''
    if col not in scraped.columns:
        scraped[col] = ''

# Concatenate
combined = pd.concat([orig[all_cols], scraped[all_cols]], ignore_index=True)

# Remove duplicates by URL, then by Title+Price
combined = combined.drop_duplicates(subset=['URL'])
combined = combined.drop_duplicates(subset=['Title','Price'])

# Clean price: remove non-numeric, convert to int, filter outliers
combined['Price'] = combined['Price'].astype(str).str.replace(r'[^0-9]', '', regex=True)
combined['Price'] = pd.to_numeric(combined['Price'], errors='coerce')
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 1000) & (combined['Price'] <= 2000000)]

# Clean category, condition, material
for col in ['Category','Condition','Material']:
    combined[col] = combined[col].fillna('').astype(str).str.title().str.strip()

# Remove rows with empty title or description
combined = combined[combined['Title'].str.len() > 5]
combined = combined[combined['Description'].str.len() > 10]

# Save
combined.to_csv('scraped_data/furniture_combined_ready.csv', index=False, encoding='utf-8-sig')

print(f"✅ Combined dataset saved: scraped_data/furniture_combined_ready.csv\nRows: {len(combined)}")
