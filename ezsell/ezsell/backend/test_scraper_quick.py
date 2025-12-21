"""
Quick test of the production scraper - just scrape 10 listings
"""
import sys
import pandas as pd
from scrape_olx_production import MobileScraper

print("="*80)
print("🧪 QUICK SCRAPER TEST - 10 Listings")
print("="*80)

# Create scraper with small target
scraper = MobileScraper(target_count=10, headless=False)

try:
    # Scrape just Samsung phones
    scraper.brands = ['samsung']  # Only one brand for quick test
    
    df = scraper.scrape()
    
    print(f"\n✅ Scraped {len(df)} listings!")
    print("\n📊 Sample Data:")
    print(df[['Title', 'Price', 'Brand', 'Location']].head(10))
    
    # Save to CSV
    output_file = 'scraped_data/test_mobile_sample.csv'
    df.to_csv(output_file, index=False)
    print(f"\n💾 Saved to: {output_file}")
    
finally:
    scraper.close()

print("\n✅ Test complete!")
