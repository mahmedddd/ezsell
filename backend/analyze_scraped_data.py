import pandas as pd

# Load scraped mobile data
mobile = pd.read_csv('scraped_data/mobile_scraped_20251221_034552.csv')

print("="*80)
print("📱 SCRAPED MOBILE DATA ANALYSIS")
print("="*80)
print(f"\nTotal rows: {len(mobile):,}")
print(f"\nColumns: {list(mobile.columns)}")
print(f"\n💰 Price Statistics:")
print(f"   Min: Rs.{mobile['Price'].min():,.0f}")
print(f"   Max: Rs.{mobile['Price'].max():,.0f}")
print(f"   Mean: Rs.{mobile['Price'].mean():,.0f}")
print(f"   Median: Rs.{mobile['Price'].median():,.0f}")

print(f"\n📊 RAM Distribution:")
print(mobile['RAM'].value_counts().head(10))

print(f"\n💾 Storage Distribution:")
print(mobile['Storage'].value_counts().head(10))

print(f"\n✨ Condition Distribution:")
print(mobile['Condition'].value_counts())

print(f"\n📱 Brand Distribution:")
print(mobile['Brand'].value_counts())

print(f"\n🔍 Sample of extracted features:")
print(mobile[['Title', 'Price', 'Brand', 'RAM', 'Storage', 'Condition']].head(10))

# Check for null values
print(f"\n❓ Missing Values:")
print(mobile.isnull().sum())
