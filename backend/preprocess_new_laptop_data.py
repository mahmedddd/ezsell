"""
Advanced preprocessing for new laptop scraped dataset
Combines NLP extraction with intelligent feature engineering
"""
import pandas as pd
import numpy as np
import re
from ml_pipeline.advanced_feature_extractor import AdvancedFeatureExtractor
from ml_pipeline.enhanced_preprocessor import EnhancedPreprocessor

def preprocess_new_laptop_data(input_file='laptop_scraped_20251221_051440.csv',
                                output_file='scraped_data/laptop_new_clean.csv'):
    """
    Preprocess the new laptop dataset with intelligent filtering and extraction
    """
    print("="*80)
    print("ADVANCED LAPTOP DATA PREPROCESSING")
    print("="*80)
    
    # Load data
    df = pd.read_csv(input_file)
    print(f"\nLoaded {len(df)} total records")
    
    # STEP 1: Filter out junk listings
    print("\n[Step 1] Filtering quality listings...")
    
    # Keep only "Featured" listings (real laptops, not accessories)
    df = df[df['Title'] == 'Featured'].copy()
    print(f"  - Kept 'Featured' listings: {len(df)} records")
    
    # Remove placeholder/scam prices (Rs.1,000-5,000)
    df = df[df['Price'] > 5000].copy()
    print(f"  - Removed placeholder prices: {len(df)} records remaining")
    
    # Remove extremely high prices (likely errors > Rs.500K)
    df = df[df['Price'] < 500000].copy()
    print(f"  - Removed price outliers: {len(df)} records remaining")
    
    # STEP 2: Extract rich features from Description
    print("\n[Step 2] Extracting features from descriptions...")
    
    extractor = AdvancedFeatureExtractor()
    
    # Extract from Description (richer than Title)
    features_list = []
    for idx, row in df.iterrows():
        # Use Description which has full specs
        text = row['Description']
        features = extractor.extract_laptop_features(text)
        features_list.append(features)
    
    features_df = pd.DataFrame(features_list)
    
    # Merge with original data
    df_clean = pd.DataFrame({
        'title': df['Description'].values,
        'price': df['Price'].values,
        'condition': df['Condition'].values,
    })
    
    # Add all extracted features
    for col in features_df.columns:
        df_clean[col] = features_df[col].values
    
    print(f"  - Extracted {len(features_df.columns)} technical features")
    
    # STEP 3: Validate extracted features
    print("\n[Step 3] Validating extracted features...")
    
    # RAM validation (2-128 GB)
    df_clean['ram'] = pd.to_numeric(df_clean['ram'], errors='coerce')
    invalid_ram = (df_clean['ram'] < 2) | (df_clean['ram'] > 128)
    df_clean.loc[invalid_ram, 'ram'] = np.nan
    
    # Storage validation (128-8192 GB)
    df_clean['storage'] = pd.to_numeric(df_clean['storage'], errors='coerce')
    invalid_storage = (df_clean['storage'] < 128) | (df_clean['storage'] > 8192)
    df_clean.loc[invalid_storage, 'storage'] = np.nan
    
    # Screen size validation (11-18 inches)
    df_clean['screen_size'] = pd.to_numeric(df_clean['screen_size'], errors='coerce')
    invalid_screen = (df_clean['screen_size'] < 11) | (df_clean['screen_size'] > 18)
    df_clean.loc[invalid_screen, 'screen_size'] = 15.6  # Default
    
    # Processor generation validation (1-14)
    df_clean['processor_generation'] = pd.to_numeric(df_clean['processor_generation'], errors='coerce').fillna(0)
    df_clean.loc[df_clean['processor_generation'] > 14, 'processor_generation'] = 0
    
    # GPU tier validation (0-5)
    df_clean['gpu_tier'] = pd.to_numeric(df_clean['gpu_tier'], errors='coerce').fillna(0)
    df_clean.loc[(df_clean['gpu_tier'] < 0) | (df_clean['gpu_tier'] > 5), 'gpu_tier'] = 0
    
    print(f"  - Validated all technical features")
    
    # STEP 4: Feature completeness analysis
    print("\n[Step 4] Feature completeness analysis...")
    
    ram_complete = (df_clean['ram'].notna() & (df_clean['ram'] > 0)).sum()
    storage_complete = (df_clean['storage'].notna() & (df_clean['storage'] > 0)).sum()
    processor_complete = (df_clean['processor_tier'].notna() & (df_clean['processor_tier'] > 0)).sum()
    gpu_complete = (df_clean['gpu_tier'].notna() & (df_clean['gpu_tier'] > 0)).sum()
    
    print(f"  - RAM detected: {ram_complete}/{len(df_clean)} ({ram_complete/len(df_clean)*100:.1f}%)")
    print(f"  - Storage detected: {storage_complete}/{len(df_clean)} ({storage_complete/len(df_clean)*100:.1f}%)")
    print(f"  - Processor detected: {processor_complete}/{len(df_clean)} ({processor_complete/len(df_clean)*100:.1f}%)")
    print(f"  - GPU detected: {gpu_complete}/{len(df_clean)} ({gpu_complete/len(df_clean)*100:.1f}%)")
    
    # STEP 5: Save preprocessed data
    print(f"\n[Step 5] Saving preprocessed data to {output_file}...")
    df_clean.to_csv(output_file, index=False)
    print(f"  - Saved {len(df_clean)} clean records")
    
    # STEP 6: Statistics
    print("\n" + "="*80)
    print("PREPROCESSING SUMMARY")
    print("="*80)
    print(f"Original dataset: 4,320 records")
    print(f"Final clean dataset: {len(df_clean)} records ({len(df_clean)/4320*100:.1f}% retention)")
    print(f"\nPrice distribution:")
    print(df_clean['price'].describe())
    print(f"\nFeature extraction success rates:")
    print(f"  RAM: {ram_complete/len(df_clean)*100:.1f}%")
    print(f"  Storage: {storage_complete/len(df_clean)*100:.1f}%")
    print(f"  Processor: {processor_complete/len(df_clean)*100:.1f}%")
    print(f"  GPU: {gpu_complete/len(df_clean)*100:.1f}%")
    
    return df_clean

if __name__ == "__main__":
    df = preprocess_new_laptop_data()
    print("\n✓ Preprocessing complete! Ready for training.")
