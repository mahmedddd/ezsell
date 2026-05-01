"""Check preprocessed data for NaN and invalid values"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("scraped_data")

for category in ['laptop', 'furniture']:
    files = list(data_dir.glob(f"{category}_preprocessed_*.csv"))
    if not files:
        print(f"❌ No {category} data found")
        continue
    
    csv_file = files[0]
    print(f"\n{'='*60}")
    print(f"📊 {category.upper()} DATA ANALYSIS")
    print(f"{'='*60}")
    print(f"File: {csv_file.name}")
    
    df = pd.read_csv(csv_file)
    
    print(f"\n📈 Basic Stats:")
    print(f"  Total rows: {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    
    print(f"\n💰 Price Column:")
    print(f"  NaN count: {df['price'].isna().sum()}")
    print(f"  Inf count: {np.isinf(df['price']).sum()}")
    print(f"  Min: {df['price'].min():,.0f}")
    print(f"  Max: {df['price'].max():,.0f}")
    print(f"  Mean: {df['price'].mean():,.0f}")
    
    # Check for NaN in all columns
    nan_counts = df.isna().sum()
    nan_cols = nan_counts[nan_counts > 0]
    
    if len(nan_cols) > 0:
        print(f"\n⚠️ Columns with NaN values:")
        for col, count in nan_cols.items():
            pct = (count / len(df)) * 100
            print(f"  {col}: {count} ({pct:.1f}%)")
    else:
        print(f"\n✅ No NaN values found")
    
    # Check for infinity
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_found = False
    for col in numeric_cols:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            if not inf_found:
                print(f"\n⚠️ Columns with Inf values:")
                inf_found = True
            print(f"  {col}: {inf_count}")
    
    if not inf_found:
        print(f"✅ No Inf values found")
    
    # Check price after outlier removal
    from scipy import stats
    z_scores = np.abs(stats.zscore(df['price']))
    clean_df = df[z_scores < 3.0]
    print(f"\n🧹 After outlier removal (Z<3.0):")
    print(f"  Rows remaining: {len(clean_df)}")
    print(f"  Price NaN: {clean_df['price'].isna().sum()}")
    print(f"  Price Inf: {np.isinf(clean_df['price']).sum()}")

print("\n" + "="*60 + "\n")
