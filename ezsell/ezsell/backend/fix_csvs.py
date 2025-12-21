import pandas as pd
import re

def fix_csv(input_path, output_path, expected_cols):
    """Fix malformed CSV with multi-line descriptions"""
    print(f"📥 Fixing: {input_path}")
    
    try:
        # Try with quoting to handle multi-line
        df = pd.read_csv(input_path, quotechar='"', escapechar='\\', on_bad_lines='skip')
        print(f"✅ Loaded {len(df):,} rows")
        
        # Clean Price column - multiply by 1000 if < 1000
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
            # Fix thousand-separated prices (298 -> 298000)
            df.loc[df['Price'] < 1000, 'Price'] = df.loc[df['Price'] < 1000, 'Price'] * 1000
            df = df[df['Price'] > 0]  # Remove invalid prices
            print(f"✅ Fixed prices: {df['Price'].min():.0f} - {df['Price'].max():.0f}")
        
        # Clean descriptions - remove newlines
        if 'Description' in df.columns:
            df['Description'] = df['Description'].fillna('').astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
        
        if 'Title' in df.columns:
            df['Title'] = df['Title'].fillna('').astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
        
        # Save cleaned CSV
        df.to_csv(output_path, index=False)
        print(f"💾 Saved {len(df):,} rows to: {output_path}\n")
        return len(df)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔧 CSV CLEANING PIPELINE")
    print("="*80 + "\n")
    
    base = r"C:\Users\ahmed\Downloads\ezsell\ezsell"
    
    # Fix laptops
    laptop_rows = fix_csv(
        f"{base}\\laptops.csv",
        f"{base}\\laptops_cleaned.csv",
        ['Title', 'Price', 'Brand', 'Model', 'Condition', 'Type', 'Description', 'URL']
    )
    
    # Fix furniture
    furniture_rows = fix_csv(
        f"{base}\\furniture.csv",
        f"{base}\\furniture_cleaned.csv",
        ['Title', 'Price', 'Description', 'Condition', 'Type', 'Material', 'URL']
    )
    
    # Copy mobiles (already clean)
    mobile_df = pd.read_csv(f"{base}\\cleaned_mobiles.csv")
    mobile_df.to_csv(f"{base}\\mobiles_cleaned.csv", index=False)
    print(f"✅ Copied {len(mobile_df):,} mobile rows\n")
    
    print("="*80)
    print(f"✅ CLEANING COMPLETE")
    print(f"   Mobiles:   {len(mobile_df):,} rows")
    print(f"   Laptops:   {laptop_rows:,} rows")
    print(f"   Furniture: {furniture_rows:,} rows")
    print("="*80)
