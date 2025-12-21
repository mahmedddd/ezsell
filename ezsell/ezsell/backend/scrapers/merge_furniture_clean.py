"""
Merge and clean furniture.csv and furniture_scraped_20251221_054515.csv
- Aligns columns (Type/Category, Material, etc.)
- Converts all prices to numeric, multiplies 3-digit prices by 100
- Deduplicates by URL and Title+Price
- Outputs furniture_merged_clean.csv
"""

import pandas as pd
import numpy as np
import re

# Load both datasets
orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

# Standardize column names
orig.columns = [c.strip().title() for c in orig.columns]
scraped.columns = [c.strip().title() for c in scraped.columns]

# Map columns to a unified schema
# Target columns: Title, Price, Category, Condition, Material, Description, URL
orig = orig.rename(columns={
    'Type': 'Category',
    'Description': 'Description',
    'Material': 'Material',
    'Condition': 'Condition',
    'Url': 'URL',
})

# Some orig rows may have missing columns, fill them
for col in ['Title','Price','Category','Condition','Material','Description','URL']:
    if col not in orig.columns:
        orig[col] = ''
    if col not in scraped.columns:
        scraped[col] = ''

# Select and order columns
cols = ['Title','Price','Category','Condition','Material','Description','URL']
orig = orig[cols]
scraped = scraped[cols]

# Merge
combined = pd.concat([orig, scraped], ignore_index=True)

# Clean price: remove non-numeric, convert to int
combined['Price'] = combined['Price'].astype(str).str.extract(r'(\d+)')[0]
combined['Price'] = pd.to_numeric(combined['Price'], errors='coerce')

# Multiply 3-digit prices by 100 (e.g. 243 -> 24300)
def fix_price(p):
    if pd.isnull(p):
        return np.nan
    if 100 <= p < 1000:
        return p * 100
    return p
combined['Price'] = combined['Price'].apply(fix_price)

# Remove rows with invalid price
combined = combined[combined['Price'].notnull()]
combined = combined[(combined['Price'] >= 1000) & (combined['Price'] <= 2000000)]

# Deduplicate by URL, then by Title+Price
combined = combined.drop_duplicates(subset=['URL'])
combined = combined.drop_duplicates(subset=['Title','Price'])

# Remove rows with empty title or description
combined = combined[combined['Title'].str.len() > 5]
combined = combined[combined['Description'].str.len() > 10]

# Save
combined.to_csv('scraped_data/furniture_merged_clean.csv', index=False, encoding='utf-8-sig')
print(f"✅ Merged dataset saved: scraped_data/furniture_merged_clean.csv\nRows: {len(combined)}")
