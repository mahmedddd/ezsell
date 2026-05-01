import csv
import pandas as pd
from pathlib import Path

def robust_csv_parse(file_path, expected_columns):
    """Manually parse CSV handling multi-line descriptions"""
    print(f"📥 Parsing: {file_path}")
    
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        # Read first line to get headers
        headers = f.readline().strip().split(',')
        print(f"📋 Headers: {headers}")
        
        current_row = []
        field_count = 0
        in_quotes = False
        current_field = ""
        
        for line in f:
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                    current_field += char
                elif char == ',' and not in_quotes:
                    current_row.append(current_field.strip('"'))
                    current_field = ""
                    field_count += 1
                else:
                    current_field += char
            
            # Check if row complete
            if not in_quotes and field_count >= expected_columns - 1:
                current_row.append(current_field.strip('"').strip())
                if len(current_row) == expected_columns:
                    rows.append(current_row)
                current_row = []
                field_count = 0
                current_field = ""
    
    print(f"✅ Parsed {len(rows):,} rows")
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers[:expected_columns])
    
    # Convert Price to numeric
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    
    # Fix thousand-prices (< 1000)
    df.loc[df['Price'] < 1000, 'Price'] = df.loc[df['Price'] < 1000, 'Price'] * 1000
    
    # Remove invalid prices
    df = df[df['Price'] > 0]
    df = df[df['Price'] < 10000000]
    
    print(f"✅ Valid rows: {len(df):,}")
    print(f"💰 Price range: {df['Price'].min():.0f} - {df['Price'].max():.0f}")
    
    return df

if __name__ == "__main__":
    base = Path(r"C:\Users\ahmed\Downloads\ezsell\ezsell")
    
    print("\n" + "="*80)
    print("🔧 ROBUST CSV PARSING")
    print("="*80 + "\n")
    
    # Parse laptops
    try:
        laptop_df = robust_csv_parse(
            base / "laptops.csv",
            expected_columns=8  # Title,Price,Brand,Model,Condition,Type,Description,URL
        )
        laptop_df.to_csv(base / "laptops_fixed.csv", index=False)
        print(f"💾 Saved to: laptops_fixed.csv\n")
    except Exception as e:
        print(f"❌ Laptop parsing failed: {e}\n")
    
    # Parse furniture
    try:
        furniture_df = robust_csv_parse(
            base / "furniture.csv",
            expected_columns=7  # Title,Price,Description,Condition,Type,Material,URL
        )
        furniture_df.to_csv(base / "furniture_fixed.csv", index=False)
        print(f"💾 Saved to: furniture_fixed.csv\n")
    except Exception as e:
        print(f"❌ Furniture parsing failed: {e}\n")
    
    # Copy mobiles
    mobile_df = pd.read_csv(base / "cleaned_mobiles.csv")
    mobile_df.to_csv(base / "mobiles_fixed.csv", index=False)
    print(f"✅ Copied {len(mobile_df):,} mobile rows")
    
    print("\n" + "="*80)
    print("✅ PARSING COMPLETE")
    print("="*80)
