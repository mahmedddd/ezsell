"""
🚀 Complete Pipeline: Preprocess + Train
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def preprocess_data():
    """Preprocess original CSV files"""
    logger.info("\n" + "="*80)
    logger.info("📊 PREPROCESSING DATA")
    logger.info("="*80)
    
    data_dir = Path("../../Data")
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    
    # Mobile
    logger.info("\n📱 Processing Mobile data...")
    mobile_df = pd.read_csv(data_dir / "cleaned_mobiles.csv")
    mobile_df = mobile_df.rename(columns={'Title': 'title', 'Price': 'price'})
    
    # Extract features
    mobile_df['ram'] = mobile_df['title'].str.extract(r'(\d+)\s*GB', expand=False).fillna(0).astype(float)
    mobile_df['storage'] = mobile_df['title'].str.extract(r'(\d+)\s*GB', expand=False).fillna(0).astype(float)
    mobile_df['battery'] = mobile_df['title'].str.extract(r'(\d{4,5})\s*mAh', expand=False).fillna(4000).astype(float)
    mobile_df['camera'] = mobile_df['title'].str.extract(r'(\d+)\s*MP', expand=False).fillna(12).astype(float)
    mobile_df['screen_size'] = mobile_df['title'].str.extract(r'(\d+\.?\d*)\s*inch', expand=False).fillna(6.0).astype(float)
    
    # Brand premium (1-10)
    brands = {'samsung': 8, 'apple': 10, 'iphone': 10, 'xiaomi': 6, 'oppo': 5, 'vivo': 5, 
              'realme': 5, 'oneplus': 8, 'huawei': 7, 'honor': 6, 'nokia': 4}
    mobile_df['brand_premium'] = 5
    for brand, score in brands.items():
        mask = mobile_df['title'].fillna('').str.lower().str.contains(brand)
        mobile_df.loc[mask, 'brand_premium'] = score
    
    # Boolean features
    mobile_df['is_5g'] = mobile_df['title'].fillna('').str.contains('5G|5g', case=False).astype(int)
    mobile_df['is_pta'] = mobile_df['title'].fillna('').str.contains('PTA|pta', case=False).astype(int)
    mobile_df['is_amoled'] = mobile_df['title'].fillna('').str.contains('AMOLED|amoled', case=False).astype(int)
    mobile_df['has_warranty'] = mobile_df['title'].fillna('').str.contains('warranty', case=False).astype(int)
    mobile_df['has_box'] = mobile_df['title'].fillna('').str.contains('box', case=False).astype(int)
    
    # Condition (1-10)
    mobile_df['condition_score'] = 8
    mobile_df.loc[mobile_df['title'].fillna('').str.contains('new|brand new', case=False), 'condition_score'] = 10
    mobile_df.loc[mobile_df['title'].fillna('').str.contains('used|old', case=False), 'condition_score'] = 6
    
    # Age
    mobile_df['age_months'] = 6
    
    mobile_output = output_dir / "mobile_preprocessed_20251213_new.csv"
    mobile_df.to_csv(mobile_output, index=False)
    logger.info(f"✅ Saved {len(mobile_df)} mobile samples → {mobile_output}")
    
    # Laptop
    logger.info("\n💻 Processing Laptop data...")
    laptop_df = pd.read_csv(data_dir / "laptops.csv")
    laptop_df = laptop_df.rename(columns={'Title': 'title', 'Price': 'price'})
    
    # Extract features
    laptop_df['ram'] = laptop_df['title'].str.extract(r'(\d+)\s*GB', expand=False).fillna(8).astype(float)
    laptop_df['storage'] = laptop_df['title'].str.extract(r'(\d+)\s*GB|(\d+)\s*TB', expand=False)[0].fillna(256).astype(float)
    laptop_df['screen_size'] = laptop_df['title'].str.extract(r'(\d+\.?\d*)\s*inch', expand=False).fillna(15.6).astype(float)
    
    # Brand premium
    laptop_brands = {'dell': 7, 'hp': 6, 'lenovo': 7, 'asus': 7, 'acer': 6, 'apple': 10, 
                     'macbook': 10, 'msi': 8, 'razer': 9, 'alienware': 9}
    laptop_df['brand_premium'] = 6
    for brand, score in laptop_brands.items():
        mask = laptop_df['title'].fillna('').str.lower().str.contains(brand)
        laptop_df.loc[mask, 'brand_premium'] = score
    
    # Processor tier
    laptop_df['processor_tier'] = 5
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('i3|core 3', case=False), 'processor_tier'] = 3
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('i5|core 5', case=False), 'processor_tier'] = 5
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('i7|core 7', case=False), 'processor_tier'] = 7
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('i9|core 9', case=False), 'processor_tier'] = 9
    
    # Generation
    gen_match = laptop_df['title'].fillna('').str.extract(r'(\d+)th\s*gen', expand=False, flags=re.IGNORECASE)
    laptop_df['generation'] = gen_match.fillna(10).astype(float)
    
    # Boolean features
    laptop_df['has_gpu'] = laptop_df['title'].fillna('').str.contains('nvidia|gtx|rtx|gpu|graphics', case=False).astype(int)
    laptop_df['gpu_tier'] = 0
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('rtx|3060|4060', case=False), 'gpu_tier'] = 8
    laptop_df.loc[laptop_df['title'].fillna('').str.contains('gtx|1650|1660', case=False), 'gpu_tier'] = 5
    
    laptop_df['is_gaming'] = laptop_df['title'].fillna('').str.contains('gaming|gamer', case=False).astype(int)
    laptop_df['is_touchscreen'] = laptop_df['title'].fillna('').str.contains('touch|touchscreen', case=False).astype(int)
    laptop_df['has_ssd'] = laptop_df['title'].fillna('').str.contains('ssd', case=False).astype(int)
    
    laptop_df['condition_score'] = 8
    laptop_df['age_months'] = 12
    
    laptop_output = output_dir / "laptop_preprocessed_20251213_new.csv"
    laptop_df.to_csv(laptop_output, index=False)
    logger.info(f"✅ Saved {len(laptop_df)} laptop samples → {laptop_output}")
    
    # Furniture
    logger.info("\n🪑 Processing Furniture data...")
    furniture_df = pd.read_csv(data_dir / "furniture.csv")
    furniture_df = furniture_df.rename(columns={'Title': 'title', 'Price': 'price'})
    
    # Material quality
    materials = {'wood': 7, 'wooden': 7, 'teak': 9, 'mahogany': 9, 'oak': 8,
                 'leather': 8, 'fabric': 5, 'metal': 6, 'plastic': 3}
    furniture_df['material_quality'] = 5
    for material, score in materials.items():
        mask = furniture_df['title'].fillna('').str.lower().str.contains(material)
        furniture_df.loc[mask, 'material_quality'] = score
    
    # Seating capacity
    furniture_df['seating_capacity'] = furniture_df['title'].str.extract(r'(\d+)\s*seater', expand=False).fillna(3).astype(float)
    
    # Dimensions (rough estimates)
    furniture_df['length'] = 150
    furniture_df['width'] = 80
    furniture_df['height'] = 85
    furniture_df['volume'] = furniture_df['length'] * furniture_df['width'] * furniture_df['height']
    
    # Boolean features
    furniture_df['is_imported'] = furniture_df['title'].fillna('').str.contains('import|imported', case=False).astype(int)
    furniture_df['is_handmade'] = furniture_df['title'].fillna('').str.contains('handmade|hand made', case=False).astype(int)
    furniture_df['has_storage'] = furniture_df['title'].fillna('').str.contains('storage|drawer', case=False).astype(int)
    furniture_df['is_modern'] = furniture_df['title'].fillna('').str.contains('modern|contemporary', case=False).astype(int)
    furniture_df['is_antique'] = furniture_df['title'].fillna('').str.contains('antique|vintage', case=False).astype(int)
    
    furniture_df['condition_score'] = 8
    
    furniture_output = output_dir / "furniture_preprocessed_20251213_new.csv"
    furniture_df.to_csv(furniture_output, index=False)
    logger.info(f"✅ Saved {len(furniture_df)} furniture samples → {furniture_output}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ PREPROCESSING COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    preprocess_data()
    
    # Now train
    logger.info("Starting training...")
    import subprocess
    subprocess.run([
        "C:/Users/ahmed/Downloads/ezsell-20251207T122001Z-3-001/.venv/Scripts/python.exe",
        "train_models.py"
    ])
