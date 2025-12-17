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
        """Enhanced laptop data preprocessing"""
        logger.info(f"Enhanced preprocessing of {len(df)} laptop records")
        
        # Create combined text
        df['combined_text'] = df['title'].fillna('') + ' ' + df.get('description', df['title']).fillna('')
        
        # Extract advanced features
        logger.info("Extracting advanced features from text...")
        extracted_features = df['combined_text'].apply(self.feature_extractor.extract_laptop_features)
        extracted_df = pd.DataFrame(extracted_features.tolist())
        
        # Merge with original data
        for col in extracted_df.columns:
            if col not in df.columns or df[col].isna().all():
                df[col] = extracted_df[col]
            else:
                df[col] = df[col].fillna(extracted_df[col])
        
        # Clean price
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'].notna()]
        df = df[df['price'] > 5000]
        df = df[df['price'] < 500000]
        
        # Feature engineering
        df = self._engineer_laptop_features(df)
        
        # Remove outliers
        df = self._remove_price_outliers(df, 'laptop')
        
        logger.info(f"Enhanced laptop preprocessing complete. Final records: {len(df)}")
        return df
    
    def preprocess_furniture_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced furniture data preprocessing"""
        logger.info(f"Enhanced preprocessing of {len(df)} furniture records")
        
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
        """Advanced laptop feature engineering"""
        
        # Fill missing values
        df['ram'] = df['ram'].fillna(df['ram'].median())
        df['storage'] = df['storage'].fillna(df['storage'].median())
        df['screen_size'] = df['screen_size'].fillna(df['screen_size'].median())
        
        # Processor score (comprehensive)
        df['processor_score'] = (
            df.get('processor_tier', 2) * 2 +
            df.get('processor_generation', 10) * 0.5 +
            df.get('processor_brand', 1)
        )
        
        # Storage score
        df['storage_score'] = (
            df['storage'] / 100 +
            df.get('storage_type_score', 1) * 5
        )
        
        # Graphics score
        df['graphics_score'] = (
            df.get('gpu_tier', 0) * 3 +
            df.get('has_dedicated_gpu', 0) * 5
        )
        
        # Gaming capability score
        df['gaming_score'] = (
            df.get('processor_tier', 2) * 2 +
            df.get('gpu_tier', 0) * 3 +
            (df['ram'] / 4) +
            df.get('is_gaming', 0) * 5
        )
        
        # Portability score
        df['portability_score'] = (
            15 - df['screen_size']  # Smaller = more portable
        ) * df.get('battery_wh', 50) / 50
        
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
