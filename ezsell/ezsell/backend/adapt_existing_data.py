"""
Adapter script to convert existing CSV data format to ML pipeline format
"""

import pandas as pd
from pathlib import Path
import sys
import re

def adapt_mobile_data(input_csv: str, output_csv: str):
    """Convert existing mobile CSV to pipeline format"""
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    print(f"Original shape: {df.shape}")
    print(f"Original columns: {df.columns.tolist()}")
    
    # Rename columns to match pipeline
    column_mapping = {
        'Title': 'title',
        'Price': 'price',
        'Brand': 'brand',
        'Condition': 'condition',
        'URL': 'url'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Add missing columns with defaults
    if 'ram' not in df.columns:
        df['ram'] = None
    if 'storage' not in df.columns:
        df['storage'] = None
    if 'battery' not in df.columns:
        df['battery'] = None
    if 'screen_size' not in df.columns:
        df['screen_size'] = None
    if 'camera' not in df.columns:
        df['camera'] = None
    if 'color' not in df.columns:
        df['color'] = None
    if 'model' not in df.columns:
        df['model'] = df['title']
    if 'location' not in df.columns:
        df['location'] = 'Pakistan'
    if 'description' not in df.columns:
        df['description'] = df['title']
    
    # Save adapted data
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved adapted data to {output_csv}")
    print(f"Final shape: {df.shape}")
    print(f"Sample data:")
    print(df[['title', 'price', 'brand', 'condition']].head())
    
    return df

def adapt_laptop_data(input_csv: str, output_csv: str):
    """Convert existing laptop CSV to pipeline format"""
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    print(f"Original shape: {df.shape}")
    print(f"Original columns: {df.columns.tolist()}")
    
    # Rename columns
    column_mapping = {
        'Title': 'title',
        'Price': 'price',
        'Brand': 'brand',
        'Condition': 'condition',
        'Processor': 'processor',
        'RAM (GB)': 'ram',
        'Storage (GB)': 'storage',
        'URL': 'url'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Extract RAM and storage from title if columns don't exist
    if 'ram' not in df.columns or df['ram'].isna().all():
        df['ram'] = df['title'].str.extract(r'(\d+)\s*gb\s*ram', flags=re.IGNORECASE)[0]
        df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
    
    if 'storage' not in df.columns or df['storage'].isna().all():
        df['storage'] = df['title'].str.extract(r'(\d+)\s*gb|\s(\d+)\s*tb', flags=re.IGNORECASE)[0]
        df['storage'] = pd.to_numeric(df['storage'], errors='coerce')
    
    # Add missing columns
    if 'processor_type' not in df.columns:
        df['processor_type'] = None
    if 'generation' not in df.columns:
        df['generation'] = None
    if 'storage_type' not in df.columns:
        df['storage_type'] = None
    if 'gpu' not in df.columns:
        df['gpu'] = None
    if 'screen_size' not in df.columns:
        df['screen_size'] = None
    if 'model' not in df.columns:
        df['model'] = df['title']
    if 'location' not in df.columns:
        df['location'] = 'Pakistan'
    if 'description' not in df.columns:
        df['description'] = df['title']
    
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved adapted data to {output_csv}")
    print(f"Final shape: {df.shape}")
    print(f"Sample data:")
    print(df[['title', 'price', 'brand', 'condition']].head())
    
    return df

def adapt_furniture_data(input_csv: str, output_csv: str):
    """Convert existing furniture CSV to pipeline format"""
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    print(f"Original shape: {df.shape}")
    print(f"Original columns: {df.columns.tolist()}")
    
    # Rename columns
    column_mapping = {
        'Title': 'title',
        'Price': 'price',
        'Condition': 'condition',
        'Type': 'type',
        'URL': 'url'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Add missing columns
    if 'material' not in df.columns:
        df['material'] = None
    if 'color' not in df.columns:
        df['color'] = None
    if 'brand' not in df.columns:
        df['brand'] = None
    if 'style' not in df.columns:
        df['style'] = None
    if 'room_type' not in df.columns:
        df['room_type'] = None
    if 'length' not in df.columns:
        df['length'] = None
    if 'width' not in df.columns:
        df['width'] = None
    if 'height' not in df.columns:
        df['height'] = None
    if 'seating_capacity' not in df.columns:
        df['seating_capacity'] = None
    if 'location' not in df.columns:
        df['location'] = 'Pakistan'
    if 'description' not in df.columns:
        df['description'] = df['title']
    
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved adapted data to {output_csv}")
    print(f"Final shape: {df.shape}")
    print(f"Sample data:")
    print(df[['title', 'price', 'condition', 'type']].head())
    
    return df

if __name__ == '__main__':
    data_dir = Path(__file__).parent.parent.parent / "Data"
    output_dir = Path(__file__).parent / "scraped_data"
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("ADAPTING EXISTING CSV DATA FOR ML PIPELINE")
    print("="*80)
    
    # Adapt mobile data
    print("\n📱 ADAPTING MOBILE DATA...")
    print("-"*80)
    try:
        mobile_in = data_dir / "cleaned_mobiles.csv"
        mobile_out = output_dir / "mobile_adapted.csv"
        adapt_mobile_data(str(mobile_in), str(mobile_out))
    except Exception as e:
        print(f"❌ Error adapting mobile data: {e}")
    
    # Adapt laptop data
    print("\n💻 ADAPTING LAPTOP DATA...")
    print("-"*80)
    try:
        laptop_in = data_dir / "laptops.csv"
        laptop_out = output_dir / "laptop_adapted.csv"
        adapt_laptop_data(str(laptop_in), str(laptop_out))
    except Exception as e:
        print(f"❌ Error adapting laptop data: {e}")
    
    # Adapt furniture data
    print("\n🛋️  ADAPTING FURNITURE DATA...")
    print("-"*80)
    try:
        furniture_in = data_dir / "furniture.csv"
        furniture_out = output_dir / "furniture_adapted.csv"
        adapt_furniture_data(str(furniture_in), str(furniture_out))
    except Exception as e:
        print(f"❌ Error adapting furniture data: {e}")
    
    print("\n" + "="*80)
    print("✅ DATA ADAPTATION COMPLETE!")
    print("="*80)
    print(f"\nAdapted files saved to: {output_dir}")
    print("\nNow run:")
    print(f"  python run_ml_pipeline.py --category mobile --skip-scraping --csv-file \"{mobile_out}\"")
