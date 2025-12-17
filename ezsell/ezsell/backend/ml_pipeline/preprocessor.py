"""
Data Preprocessing Pipeline for Price Prediction Models
Handles cleaning, feature engineering, and encoding for mobile, laptop, and furniture data
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
import logging
from typing import Dict, List, Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocessor for price prediction data"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        
    def preprocess_mobile_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess mobile phone data"""
        logger.info(f"Preprocessing {len(df)} mobile records")
        
        # Create a copy
        df = df.copy()
        
        # Remove rows with no price
        df = df[df['price'].notna()]
        df = df[df['price'] > 0]
        
        # Handle brand
        df['brand'] = df['brand'].fillna('Unknown')
        df['brand'] = df['brand'].apply(lambda x: self._normalize_brand(x, 'mobile'))
        
        # Handle condition
        df['condition'] = df['condition'].fillna('Used')
        df['condition'] = df['condition'].apply(lambda x: 'New' if 'new' in str(x).lower() else 'Used')
        
        # Handle RAM
        df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
        df['ram'] = df['ram'].fillna(df['ram'].median())
        
        # Handle Storage
        df['storage'] = pd.to_numeric(df['storage'], errors='coerce')
        df['storage'] = df['storage'].fillna(df['storage'].median())
        
        # Handle Battery
        df['battery'] = pd.to_numeric(df['battery'], errors='coerce')
        df['battery'] = df['battery'].fillna(df['battery'].median())
        
        # Handle Screen Size
        df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce')
        df['screen_size'] = df['screen_size'].fillna(df['screen_size'].median())
        
        # Handle Camera
        df['camera'] = pd.to_numeric(df['camera'], errors='coerce')
        df['camera'] = df['camera'].fillna(df['camera'].median())
        
        # Feature engineering: RAM to Storage ratio
        df['ram_storage_ratio'] = df['ram'] / df['storage']
        
        # Feature: Total capacity score
        df['capacity_score'] = (df['ram'] * 2 + df['storage'] + df['battery'] / 1000)
        
        # Feature: Brand premium (based on average prices)
        brand_avg = df.groupby('brand')['price'].mean()
        df['brand_premium'] = df['brand'].map(brand_avg)
        
        # Feature: Age estimation (New vs Used price difference)
        df['age_factor'] = df['condition'].apply(lambda x: 1.0 if x == 'New' else 0.7)
        
        # Handle outliers in price
        df = self._remove_price_outliers(df)
        
        logger.info(f"Mobile preprocessing complete. Final records: {len(df)}")
        return df
    
    def preprocess_laptop_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess laptop data"""
        logger.info(f"Preprocessing {len(df)} laptop records")
        
        df = df.copy()
        
        # Remove rows with no price
        df = df[df['price'].notna()]
        df = df[df['price'] > 0]
        
        # Handle brand
        df['brand'] = df['brand'].fillna('Unknown')
        df['brand'] = df['brand'].apply(lambda x: self._normalize_brand(x, 'laptop'))
        
        # Handle condition
        df['condition'] = df['condition'].fillna('Used')
        df['condition'] = df['condition'].apply(lambda x: 'New' if 'new' in str(x).lower() else 'Used')
        
        # Handle processor type
        df['processor_type'] = df['processor_type'].fillna('Unknown')
        
        # Handle generation - extract number
        df['generation'] = df['generation'].apply(self._extract_generation_number)
        df['generation'] = pd.to_numeric(df['generation'], errors='coerce')
        df['generation'] = df['generation'].fillna(df['generation'].median())
        
        # Handle RAM
        df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
        df['ram'] = df['ram'].fillna(df['ram'].median())
        
        # Handle Storage
        df['storage'] = pd.to_numeric(df['storage'], errors='coerce')
        df['storage'] = df['storage'].fillna(df['storage'].median())
        
        # Handle storage type
        df['storage_type'] = df['storage_type'].fillna('HDD')
        df['is_ssd'] = df['storage_type'].apply(lambda x: 1 if 'SSD' in str(x) else 0)
        
        # Handle GPU - create has_dedicated_gpu feature
        df['has_gpu'] = df['gpu'].apply(lambda x: 1 if pd.notna(x) and 'Integrated' not in str(x) else 0)
        
        # Handle screen size
        df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce')
        df['screen_size'] = df['screen_size'].fillna(df['screen_size'].median())
        
        # Feature engineering
        df['ram_storage_ratio'] = df['ram'] / df['storage']
        df['capacity_score'] = (df['ram'] * 3 + df['storage'] / 10)
        
        # Brand premium
        brand_avg = df.groupby('brand')['price'].mean()
        df['brand_premium'] = df['brand'].map(brand_avg)
        
        # Processor score (higher generation = better)
        df['processor_score'] = df['generation'] * 10
        
        # Age factor
        df['age_factor'] = df['condition'].apply(lambda x: 1.0 if x == 'New' else 0.65)
        
        # Handle outliers
        df = self._remove_price_outliers(df)
        
        logger.info(f"Laptop preprocessing complete. Final records: {len(df)}")
        return df
    
    def preprocess_furniture_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess furniture data"""
        logger.info(f"Preprocessing {len(df)} furniture records")
        
        df = df.copy()
        
        # Remove rows with no price
        df = df[df['price'].notna()]
        df = df[df['price'] > 0]
        
        # Handle type
        df['type'] = df['type'].fillna('Other')
        
        # Handle condition
        df['condition'] = df['condition'].fillna('Used')
        df['condition'] = df['condition'].apply(lambda x: 'New' if 'new' in str(x).lower() else 'Used')
        
        # Handle material
        df['material'] = df['material'].fillna('Unknown')
        
        # Create material quality score
        material_scores = {
            'Wood': 5, 'Leather': 5, 'Marble': 4, 'Metal': 4,
            'Glass': 3, 'Fabric': 3, 'MDF': 2, 'Plastic': 1, 'Unknown': 2
        }
        df['material_quality'] = df['material'].apply(lambda x: material_scores.get(str(x).title(), 2))
        
        # Handle dimensions
        df['length'] = pd.to_numeric(df['length'], errors='coerce')
        df['width'] = pd.to_numeric(df['width'], errors='coerce')
        df['height'] = pd.to_numeric(df['height'], errors='coerce')
        
        # Calculate volume if dimensions available
        df['volume'] = df['length'] * df['width'] * df['height']
        df['volume'] = df['volume'].fillna(0)
        
        # Handle seating capacity
        df['seating_capacity'] = pd.to_numeric(df['seating_capacity'], errors='coerce')
        df['seating_capacity'] = df['seating_capacity'].fillna(0)
        
        # Feature engineering
        # Type premium
        type_avg = df.groupby('type')['price'].mean()
        df['type_premium'] = df['type'].map(type_avg)
        
        # Size score
        df['size_score'] = df['volume'].apply(lambda x: np.log1p(x) if x > 0 else 0)
        
        # Capacity score
        df['capacity_score'] = df['seating_capacity'] * df['material_quality']
        
        # Age factor
        df['age_factor'] = df['condition'].apply(lambda x: 1.0 if x == 'New' else 0.6)
        
        # Brand factor
        df['has_brand'] = df['brand'].apply(lambda x: 1 if pd.notna(x) and x != 'Unknown' else 0)
        
        # Handle outliers
        df = self._remove_price_outliers(df)
        
        logger.info(f"Furniture preprocessing complete. Final records: {len(df)}")
        return df
    
    def _normalize_brand(self, brand: str, category: str) -> str:
        """Normalize brand names"""
        if pd.isna(brand) or brand == 'Unknown':
            return 'Unknown'
        
        brand = str(brand).strip().title()
        
        # Common variations
        brand_map = {
            'Iphone': 'Apple',
            'Macbook': 'Apple',
            'Redmi': 'Xiaomi',
            'Poco': 'Xiaomi',
            'Mi': 'Xiaomi',
            'Hp': 'HP',
            'Dell Inspiron': 'Dell',
            'Dell Latitude': 'Dell'
        }
        
        return brand_map.get(brand, brand)
    
    def _extract_generation_number(self, gen_text: str) -> float:
        """Extract generation number from text"""
        if pd.isna(gen_text):
            return np.nan
        
        match = re.search(r'(\d+)', str(gen_text))
        if match:
            return float(match.group(1))
        return np.nan
    
    def _remove_price_outliers(self, df: pd.DataFrame, column: str = 'price') -> pd.DataFrame:
        """Remove price outliers using IQR method"""
        Q1 = df[column].quantile(0.05)
        Q3 = df[column].quantile(0.95)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        before = len(df)
        df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
        after = len(df)
        
        logger.info(f"Removed {before - after} outliers ({(before-after)/before*100:.1f}%)")
        return df
    
    def prepare_features(self, df: pd.DataFrame, category: str) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare final feature set for training"""
        logger.info(f"Preparing features for {category}")
        
        if category == 'mobile':
            feature_cols = [
                'brand', 'condition', 'ram', 'storage', 'battery', 
                'screen_size', 'camera', 'ram_storage_ratio', 
                'capacity_score', 'age_factor'
            ]
        elif category == 'laptop':
            feature_cols = [
                'brand', 'condition', 'processor_type', 'generation', 
                'ram', 'storage', 'is_ssd', 'has_gpu', 'screen_size',
                'ram_storage_ratio', 'capacity_score', 'processor_score', 'age_factor'
            ]
        else:  # furniture
            feature_cols = [
                'type', 'condition', 'material', 'material_quality',
                'volume', 'seating_capacity', 'size_score', 
                'capacity_score', 'age_factor', 'has_brand'
            ]
        
        # Ensure all columns exist
        for col in feature_cols:
            if col not in df.columns:
                logger.warning(f"Column {col} not found, filling with default")
                df[col] = 0
        
        # Encode categorical variables
        categorical_cols = df[feature_cols].select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))
        
        # Fill any remaining NaN values with 0
        df[feature_cols] = df[feature_cols].fillna(0)
        
        # Ensure all values are numeric
        for col in feature_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        logger.info(f"Features prepared: {len(feature_cols)} features")
        logger.info(f"NaN count after preparation: {df[feature_cols].isna().sum().sum()}")
        return df[feature_cols], feature_cols
    
    def save_to_csv(self, df: pd.DataFrame, filepath: str):
        """Save preprocessed data to CSV"""
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} records to {filepath}")
