"""
Enhanced Preprocessor with Advanced Feature Engineering
Uses NLP, regex, and sophisticated feature extraction for 70%+ accuracy
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Tuple, List, Dict
import logging
from .advanced_feature_extractor import AdvancedFeatureExtractor

logger = logging.getLogger(__name__)

class EnhancedPreprocessor:
    """Enhanced preprocessing with advanced feature extraction"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scalers = {}
        self.feature_extractor = AdvancedFeatureExtractor()
        
    def preprocess_mobile_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced mobile data preprocessing"""
        logger.info(f"Enhanced preprocessing of {len(df)} mobile records")
        
        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Create combined text for feature extraction
        df['combined_text'] = df['title'].fillna('') + ' ' + df.get('description', df['title']).fillna('')
        
        # Extract advanced features from text
        logger.info("Extracting advanced features from text...")
        extracted_features = df['combined_text'].apply(self.feature_extractor.extract_mobile_features)
        extracted_df = pd.DataFrame(extracted_features.tolist())
        
        # Merge with original data
        for col in extracted_df.columns:
            if col not in df.columns or df[col].isna().all():
                df[col] = extracted_df[col]
            else:
                # Fill missing values from extracted features
                df[col] = df[col].fillna(extracted_df[col])
        
        # Clean price
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Remove invalid prices
        df = df[df['price'].notna()]
        df = df[df['price'] > 1000]  # Min price
        df = df[df['price'] < 1000000]  # Max price
        
        # Feature engineering
        df = self._engineer_mobile_features(df)
        
        # Remove outliers
        df = self._remove_price_outliers(df, 'mobile')
        
        logger.info(f"Enhanced mobile preprocessing complete. Final records: {len(df)}")
        return df
    
    def preprocess_laptop_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced laptop data preprocessing with validation"""
        logger.info(f"Enhanced preprocessing of {len(df)} laptop records")
        
        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Use title only for extraction (descriptions often contain noise)
        logger.info("Extracting advanced features from title only...")
        extracted_features = df['title'].fillna('').apply(self.feature_extractor.extract_laptop_features)
        extracted_df = pd.DataFrame(extracted_features.tolist())
        
        # Merge with original data
        for col in extracted_df.columns:
            if col not in df.columns or df[col].isna().all():
                df[col] = extracted_df[col]
            else:
                df[col] = df[col].fillna(extracted_df[col])
        
        # VALIDATION: Clean extracted features
        logger.info("Validating and cleaning extracted features...")
        
        # Validate and cap RAM (2-128 GB for laptops)
        df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
        df.loc[df['ram'] < 2, 'ram'] = np.nan
        df.loc[df['ram'] > 128, 'ram'] = np.nan
        
        # Validate and cap Storage (128-8192 GB)
        df['storage'] = pd.to_numeric(df['storage'], errors='coerce')
        df.loc[df['storage'] < 128, 'storage'] = np.nan
        df.loc[df['storage'] > 8192, 'storage'] = np.nan
        
        # Validate screen size (11-18 inches for laptops)
        df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce')
        df.loc[df['screen_size'] < 11, 'screen_size'] = 15.6  # Default
        df.loc[df['screen_size'] > 18, 'screen_size'] = 15.6  # Default
        
        # Validate processor generation (1-14)
        df['processor_generation'] = pd.to_numeric(df['processor_generation'], errors='coerce').fillna(0)
        df.loc[df['processor_generation'] > 14, 'processor_generation'] = 0
        
        # Validate GPU tier (0-5)
        df['gpu_tier'] = pd.to_numeric(df['gpu_tier'], errors='coerce').fillna(0)
        df.loc[df['gpu_tier'] > 5, 'gpu_tier'] = 0
        df.loc[df['gpu_tier'] < 0, 'gpu_tier'] = 0
        
        # Clean price
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'].notna()]
        df = df[df['price'] > 5000]  # Minimum laptop price
        df = df[df['price'] < 500000]  # Maximum reasonable price
        
        logger.info(f"After validation: {len(df)} records (no strict filtering - training on real data)")
        
        # Feature engineering
        df = self._engineer_laptop_features(df)
        
        # Remove statistical outliers in price
        df = self._remove_price_outliers(df, 'laptop')
        
        logger.info(f"Enhanced laptop preprocessing complete. Final records: {len(df)}")
        return df
    
    def preprocess_furniture_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced furniture data preprocessing"""
        logger.info(f"Enhanced preprocessing of {len(df)} furniture records")
        
        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Create combined text
        df['combined_text'] = df['title'].fillna('') + ' ' + df.get('description', df['title']).fillna('')
        
        # Extract advanced features
        logger.info("Extracting advanced features from text...")
        extracted_features = df['combined_text'].apply(self.feature_extractor.extract_furniture_features)
        extracted_df = pd.DataFrame(extracted_features.tolist())
        
        # Merge
        for col in extracted_df.columns:
            if col not in df.columns or df[col].isna().all():
                df[col] = extracted_df[col]
            else:
                df[col] = df[col].fillna(extracted_df[col])
        
        # Clean price
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'].notna()]
        df = df[df['price'] > 1000]
        df = df[df['price'] < 300000]
        
        # Feature engineering
        df = self._engineer_furniture_features(df)
        
        # Remove outliers
        df = self._remove_price_outliers(df, 'furniture')
        
        logger.info(f"Enhanced furniture preprocessing complete. Final records: {len(df)}")
        return df
    
    def _engineer_mobile_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced mobile feature engineering"""
        
        # Fill missing values with intelligent defaults
        df['ram'] = df['ram'].fillna(df['ram'].median())
        df['storage'] = df['storage'].fillna(df['storage'].median())
        df['battery'] = df['battery'].fillna(df['battery'].median())
        df['camera'] = df['camera'].fillna(df['camera'].median())
        df['screen_size'] = df['screen_size'].fillna(df['screen_size'].median())
        
        # Advanced ratios and scores
        df['ram_storage_ratio'] = df['ram'] / (df['storage'] + 1)
        df['storage_per_price'] = df['storage'] / (df['price'] + 1)
        df['ram_per_price'] = df['ram'] / (df['price'] + 1)
        
        # Capacity score (weighted combination)
        df['capacity_score'] = (
            df['ram'] * 0.3 + 
            df['storage'] / 10 * 0.3 + 
            df['battery'] / 100 * 0.2 +
            df['camera'] * 0.1 +
            df['screen_size'] * 2 * 0.1
        )
        
        # Technology score
        df['tech_score'] = (
            df.get('is_5g', 0) * 3 +
            df.get('is_amoled', 0) * 2 +
            df.get('processor_type', 0) +
            df.get('is_pta', 0)
        )
        
        # Completeness score (accessories, warranty, etc.)
        df['completeness_score'] = (
            df.get('with_box', 0) +
            df.get('with_charger', 0) +
            df.get('with_accessories', 0) +
            df.get('has_warranty', 0) * 2
        )
        
        # Age-based depreciation
        current_year = 2025
        df['age'] = current_year - df.get('model_year', current_year)
        df['age_factor'] = np.exp(-0.1 * df['age'])  # Exponential decay
        
        # Price per GB (storage)
        df['price_per_gb'] = df['price'] / (df['storage'] + 1)
        
        # Brand premium interaction with specs
        df['premium_ram_interaction'] = df.get('brand_premium', 3) * df['ram']
        df['premium_storage_interaction'] = df.get('brand_premium', 3) * df['storage']
        
        return df
    
    def _engineer_laptop_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced laptop feature engineering with improved validation"""
        
        # Fill missing values with intelligent defaults
        ram_median = df['ram'].median() if df['ram'].notna().sum() > 0 else 8
        storage_median = df['storage'].median() if df['storage'].notna().sum() > 0 else 512
        screen_median = df['screen_size'].median() if df['screen_size'].notna().sum() > 0 else 15.6
        
        df['ram'] = df['ram'].fillna(ram_median)
        df['storage'] = df['storage'].fillna(storage_median)
        df['screen_size'] = df['screen_size'].fillna(screen_median)
        
        # Processor score (comprehensive)
        df['processor_score'] = (
            df.get('processor_tier', 2).fillna(2) * 3 +  # Tier is most important
            df.get('processor_generation', 0).fillna(0) * 1.5 +  # Generation matters
            df.get('processor_brand', 1).fillna(1) * 2  # Brand premium
        )
        
        # Storage score (capacity + type)
        df['storage_score'] = (
            df['storage'] / 50 +  # Normalize storage
            df.get('storage_type_score', 1).fillna(1) * 10  # SSD vs HDD very important
        )
        
        # Graphics score
        df['graphics_score'] = (
            df.get('gpu_tier', 0).fillna(0) * 5 +  # GPU tier is critical
            df.get('has_dedicated_gpu', 0).fillna(0) * 10  # Dedicated GPU is valuable
        )
        
        # Gaming capability score
        df['gaming_score'] = (
            df.get('processor_tier', 2).fillna(2) * 2 +
            df.get('gpu_tier', 0).fillna(0) * 4 +  # GPU more important for gaming
            (df['ram'] / 4) +
            df.get('is_gaming', 0).fillna(0) * 8  # Gaming branding
        )
        
        # Portability score (smaller + better battery = more portable)
        df['portability_score'] = (
            (17 - df['screen_size']).clip(0, 6) * 2 +  # Smaller is better
            df.get('battery_wh', 50).fillna(50) / 10
        )
        
        # Features score
        df['features_score'] = (
            df.get('is_touchscreen', 0) * 2 +
            df.get('is_2in1', 0) * 3 +
            df.get('has_backlit', 0) +
            df.get('is_fullhd', 0) * 2 +
            df.get('is_4k', 0) * 4
        )
        
        # Capacity score
        df['capacity_score'] = (
            df['ram'] * 0.4 +
            df['storage'] / 50 * 0.3 +
            df['processor_score'] * 0.3
        )
        
        # Age factor
        current_year = 2025
        df['age'] = current_year - df.get('model_year', current_year)
        df['age_factor'] = np.exp(-0.15 * df['age'])
        
        # Brand interactions
        df['premium_spec_score'] = (
            df.get('brand_premium', 3) * 
            (df['ram'] + df['storage']/100 + df['processor_score'])
        )
        
        return df
    
    def _engineer_furniture_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced furniture feature engineering"""
        
        # Fill missing values
        df['seating_capacity'] = df.get('seating_capacity', 0).fillna(0)
        df['length'] = df.get('length').fillna(df.get('length', 100).median())
        df['width'] = df.get('width').fillna(df.get('width', 50).median())
        df['height'] = df.get('height').fillna(df.get('height', 50).median())
        df['volume'] = df.get('volume').fillna(df['length'] * df['width'] * df['height'])
        
        # Size score
        df['size_score'] = np.log1p(df['volume'])
        
        # Material quality score
        df['material_score'] = (
            df.get('material_quality', 2) * 2 +
            df.get('material_type', 0)
        )
        
        # Style score
        df['style_score'] = (
            df.get('is_modern', 0) * 2 +
            df.get('is_antique', 0) * 3 +
            df.get('is_imported', 0) * 2
        )
        
        # Completeness score
        df['completeness_score'] = (
            df.get('with_cushions', 0) +
            df.get('has_warranty', 0) * 2 +
            df.get('has_brand', 0) * 2
        )
        
        # Quality score (combined)
        df['quality_score'] = (
            df.get('condition_score', 5) +
            df['material_score'] +
            df.get('is_handmade', 0) * 3
        )
        
        # Capacity score
        df['capacity_score'] = df['seating_capacity'] * df['size_score']
        
        # Price per volume
        df['price_per_volume'] = df['price'] / (df['volume'] + 1)
        
        # Type-material interaction
        df['type_material_score'] = df.get('furniture_type', 0) * df['material_score']
        
        return df
    
    def _remove_price_outliers(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        """Remove price outliers using IQR method"""
        initial_count = len(df)
        
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
        
        removed = initial_count - len(df)
        logger.info(f"Removed {removed} outliers ({removed/initial_count*100:.1f}%)")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame, category: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare enhanced feature set for training"""
        logger.info(f"Preparing enhanced features for {category}")
        
        if category == 'mobile':
            feature_cols = [
                'ram', 'storage', 'battery', 'camera', 'screen_size',
                'ram_storage_ratio', 'storage_per_price', 'ram_per_price',
                'capacity_score', 'tech_score', 'completeness_score',
                'age_factor', 'price_per_gb', 'premium_ram_interaction',
                'premium_storage_interaction', 'condition_score',
                'is_pta', 'non_pta', 'is_5g', 'is_amoled',
                'brand_premium', 'processor_type', 'with_box', 'has_warranty'
            ]
        elif category == 'laptop':
            feature_cols = [
                'ram', 'storage', 'screen_size',
                'processor_score', 'storage_score', 'graphics_score',
                'gaming_score', 'portability_score', 'features_score',
                'capacity_score', 'age_factor', 'premium_spec_score',
                'condition_score', 'processor_tier', 'processor_generation',
                'gpu_tier', 'has_dedicated_gpu', 'is_gaming',
                'is_touchscreen', 'is_fullhd', 'is_4k',
                'brand_premium', 'has_warranty', 'storage_type_score'
            ]
        else:  # furniture
            feature_cols = [
                'volume', 'length', 'width', 'height', 'seating_capacity',
                'size_score', 'material_score', 'style_score',
                'completeness_score', 'quality_score', 'capacity_score',
                'price_per_volume', 'type_material_score', 'condition_score',
                'furniture_type', 'material_quality', 'material_type',
                'is_sofa', 'is_bed', 'is_table', 'is_chair',
                'is_imported', 'is_antique', 'has_brand'
            ]
        
        # Ensure all columns exist
        for col in feature_cols:
            if col not in df.columns:
                logger.warning(f"Column {col} not found, filling with 0")
                df[col] = 0
        
        # Fill any remaining NaN values
        for col in feature_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        X = df[feature_cols].copy()
        y = df['price'].copy()
        
        # Ensure no NaN in features or target
        X = X.fillna(0)
        
        logger.info(f"Enhanced features prepared: {len(feature_cols)} features")
        logger.info(f"NaN count after preparation: {X.isna().sum().sum()}")
        logger.info(f"Final dataset: {len(X)} samples")
        
        return X, y, feature_cols
