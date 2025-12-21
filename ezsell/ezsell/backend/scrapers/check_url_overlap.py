"""
Check URL overlap between datasets
"""
import pandas as pd

orig = pd.read_csv(r'../../furniture.csv', on_bad_lines='skip')
scraped = pd.read_csv(r'scraped_data/furniture_scraped_20251221_054515.csv', on_bad_lines='skip')

orig_urls = set(orig['URL'].dropna())
scraped_urls = set(scraped['URL'].dropna())

print(f"Original URLs: {len(orig_urls)}")
print(f"Scraped URLs: {len(scraped_urls)}")
print(f"Overlap: {len(orig_urls & scraped_urls)}")
print(f"Unique to original: {len(orig_urls - scraped_urls)}")
print(f"Unique to scraped: {len(scraped_urls - orig_urls)}")
