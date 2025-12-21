"""
Advanced Price Prediction API - Production Ready
Uses new advanced models: XGBoost for laptops (92.29% R²), Gradient Boosting for mobile/furniture (99.9%+ R²)
Includes strict title validation to prevent irrelevant predictions
"""

from fastapi import APIRouter, HTTPException
import pickle
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Optional, List, Tuple
import logging

from schemas.schemas import PricePredictionRequest, PricePredictionResponse
from advanced_laptop_preprocessor import AdvancedLaptopPreprocessor
from utils.title_validator import TitleValidator

logger = logging.getLogger(__name__)
router = APIRouter()

# Model paths
MODELS_DIR = Path(__file__).parent.parent / "models_enhanced"

# Cache loaded models
_loaded_models = {}

def load_advanced_model(category: str) -> Optional[Dict[str, Any]]:
    """Load advanced production model - handles both dict and direct model formats"""
    if category in _loaded_models:
        return _loaded_models[category]
    
    try:
        # Determine which model file to use
        if category == 'laptop':
            model_file = MODELS_DIR / "price_predictor_laptop_ADVANCED.pkl"
        elif category == 'mobile':
            model_file = MODELS_DIR / "price_predictor_mobile_enhanced.pkl"
        elif category == 'furniture':
            model_file = MODELS_DIR / "price_predictor_furniture_enhanced.pkl"
        else:
            logger.error(f"Invalid category: {category}")
            return None
        
        if not model_file.exists():
            logger.error(f"Model file not found: {model_file}")
            return None
        
        # Load model file using joblib (handles both pickle and joblib formats)
        try:
            loaded_data = joblib.load(model_file)
        except Exception as e:
            # Fallback to pickle if joblib fails
            logger.warning(f"Joblib load failed, trying pickle: {e}")
            with open(model_file, 'rb') as f:
                loaded_data = pickle.load(f)
        
        # Handle different model formats
        if isinstance(loaded_data, dict):
            # Format 1: Dict with 'model', 'scaler', 'metadata' (laptop format)
            if 'model' in loaded_data:
                model_data = loaded_data
                logger.info(f"Loaded {category} model (dict format): {type(model_data['model']).__name__}")
            else:
                logger.error(f"Invalid dict structure for {category}")
                return None
        else:
            # Format 2: Direct model object (mobile/furniture format)
            # Wrap in dict structure for consistency
            model_data = {
                'model': loaded_data,
                'scaler': None,  # These models don't use scalers
                'metadata': {}
            }
            logger.info(f"Loaded {category} model (direct format): {type(loaded_data).__name__}")
        
        # Load metadata from JSON file
        metadata_file = MODELS_DIR / f"model_metadata_{category}_{'ADVANCED' if category == 'laptop' else 'enhanced'}.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                model_data['metadata'] = json.load(f)
        
        _loaded_models[category] = model_data
        
        return model_data
    
    except Exception as e:
        logger.error(f"Error loading model for {category}: {e}")
        return None


def prepare_laptop_features_advanced(data: Dict[str, Any]) -> np.ndarray:
    """Prepare laptop features using advanced preprocessor"""
    
    # Create combined text from title and description
    text = f"{data.get('title', '')} {data.get('description', '')}"
    condition = data.get('condition', 'Used')
    
    # Initialize preprocessor
    preprocessor = AdvancedLaptopPreprocessor()
    
    # Extract features
    features = {}
    
    # Brand features
    brand, brand_score = preprocessor.extract_brand(text)
    features['brand'] = brand
    features['brand_score'] = brand_score
    
    # RAM (improved extraction)
    features['ram'] = preprocessor.extract_ram_improved(text)
    
    # Storage (improved extraction)
    storage_gb, storage_type, storage_score = preprocessor.extract_storage_improved(text)
    features['storage_gb'] = storage_gb
    features['storage_type'] = storage_type
    features['storage_score'] = storage_score
    features['is_ssd'] = 1 if storage_type in ['ssd', 'nvme', 'm.2', 'm2'] else 0
    
    # Processor (improved extraction)
    proc = preprocessor.extract_processor_improved(text)
    features['processor_tier'] = proc['tier']
    features['processor_brand'] = proc['brand']
    features['processor_generation'] = proc['generation']
    features['processor_model'] = proc['model']
    features['processor_score'] = proc['score']
    
    # GPU (improved extraction)
    gpu = preprocessor.extract_gpu_improved(text)
    features['gpu_tier'] = gpu['tier']
    features['has_dedicated_gpu'] = gpu['has_dedicated']
    features['is_gaming_gpu'] = gpu['is_gaming']
    features['gpu_vram'] = gpu['vram']
    features['gpu_score'] = gpu['score']
    
    # Display features
    display = preprocessor.extract_display_features(text)
    features.update(display)
    
    # Condition features
    cond = preprocessor.extract_condition_features(text, condition)
    features.update(cond)
    
    # Special features
    special = preprocessor.extract_special_features(text)
    features.update(special)
    
    # Text features
    features['text_length'] = len(text)
    features['word_count'] = len(text.split())
    
    # Composite scores
    features['total_specs_score'] = (
        features['processor_score'] + 
        features['storage_score'] + 
        features['gpu_score'] + 
        (features['ram'] or 0) * 10 +
        features['condition_score'] * 5
    )
    
    # Create feature array matching training order (44 features)
    feature_order = [
        'brand_score', 'ram', 'storage_gb', 'storage_score', 'is_ssd',
        'processor_tier', 'processor_brand', 'processor_generation', 'processor_score',
        'gpu_tier', 'has_dedicated_gpu', 'is_gaming_gpu', 'gpu_vram', 'gpu_score',
        'screen_size', 'is_fullhd', 'is_2k', 'is_4k', 'is_touchscreen', 'refresh_rate',
        'condition_score', 'is_new', 'is_used', 'has_warranty', 'age_years', 'age_penalty',
        'is_gaming', 'is_2in1', 'is_premium', 'has_backlit', 'has_fingerprint',
        'has_webcam', 'battery_wh', 'weight_kg',
        'text_length', 'word_count', 'total_specs_score'
    ]
    
    # Fill missing values
    if features['ram'] is None:
        features['ram'] = 8
    if features['storage_gb'] is None:
        features['storage_gb'] = 256
    if features['gpu_vram'] is None:
        features['gpu_vram'] = 0
    if features['battery_wh'] is None:
        features['battery_wh'] = 45
    if features['weight_kg'] is None:
        features['weight_kg'] = 2.0
    
    # Create feature vector
    feature_vector = []
    for feat in feature_order:
        value = features.get(feat, 0)
        feature_vector.append(value if value is not None else 0)
    
    # Add engineered features (same as training)
    ram = feature_vector[1]
    storage_gb = feature_vector[2]
    processor_score = feature_vector[8]
    gpu_score = feature_vector[13]
    condition_score = feature_vector[20]
    is_premium = feature_vector[28]
    brand_score = feature_vector[0]
    total_specs_score = feature_vector[36]
    age_years = feature_vector[24]
    gpu_vram = feature_vector[12]
    is_gaming = feature_vector[26]
    
    # Additional engineered features
    feature_vector.append(ram / (storage_gb + 1))  # ram_storage_ratio
    feature_vector.append(processor_score * gpu_score)  # processor_gpu_combo
    feature_vector.append(brand_score * condition_score * (is_premium + 1))  # premium_score
    feature_vector.append(is_gaming * (gpu_score + processor_score))  # gaming_score
    feature_vector.append(ram + (gpu_vram * 2))  # total_memory
    feature_vector.append(total_specs_score / (age_years + 1))  # specs_per_age
    feature_vector.append((processor_score + ram * 5 + storage_gb / 10) * condition_score)  # value_indicator
    
    return np.array([feature_vector])


def prepare_mobile_features(data: Dict[str, Any]) -> pd.DataFrame:
    """Prepare mobile features (use existing enhanced preprocessor)"""
    from ml_pipeline.enhanced_preprocessor import EnhancedPreprocessor
    
    # Create DataFrame from input
    df_input = pd.DataFrame([{
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'price': 0  # Placeholder
    }])
    
    preprocessor = EnhancedPreprocessor()
    X, _, _ = preprocessor.prepare_features(df_input, 'mobile')
    
    return X


# Realistic market prices for Pakistani market (December 2024)
MOBILE_MARKET_PRICES = {
    # Samsung Galaxy S Series (Flagships)
    's24 ultra': {'base': 350000, 'new': 400000},
    's24 plus': {'base': 280000, 'new': 320000},
    's24': {'base': 220000, 'new': 260000},
    's23 ultra': {'base': 280000, 'new': 320000},
    's23 plus': {'base': 200000, 'new': 240000},
    's23': {'base': 150000, 'new': 180000},
    's22 ultra': {'base': 180000, 'new': 220000},
    's22 plus': {'base': 130000, 'new': 160000},
    's22': {'base': 100000, 'new': 130000},
    's21 ultra': {'base': 130000, 'new': 160000},
    's21 plus': {'base': 90000, 'new': 110000},
    's21': {'base': 70000, 'new': 90000},
    's21 fe': {'base': 60000, 'new': 75000},
    's20 ultra': {'base': 90000, 'new': 110000},
    's20 plus': {'base': 70000, 'new': 85000},
    's20': {'base': 55000, 'new': 70000},
    's20 fe': {'base': 45000, 'new': 55000},
    
    # Samsung Galaxy Z Series (Foldables)
    'z fold 5': {'base': 380000, 'new': 450000},
    'z fold 4': {'base': 280000, 'new': 330000},
    'z fold 3': {'base': 180000, 'new': 220000},
    'z flip 5': {'base': 220000, 'new': 270000},
    'z flip 4': {'base': 150000, 'new': 180000},
    'z flip 3': {'base': 90000, 'new': 110000},
    
    # Samsung Galaxy A Series
    'a54': {'base': 65000, 'new': 80000},
    'a53': {'base': 50000, 'new': 62000},
    'a52': {'base': 40000, 'new': 50000},
    'a34': {'base': 50000, 'new': 60000},
    'a33': {'base': 40000, 'new': 48000},
    'a24': {'base': 38000, 'new': 45000},
    'a23': {'base': 32000, 'new': 38000},
    'a14': {'base': 28000, 'new': 35000},
    'a13': {'base': 24000, 'new': 30000},
    'a04': {'base': 20000, 'new': 25000},
    'a03': {'base': 18000, 'new': 22000},
    
    # Samsung Galaxy M Series
    'm54': {'base': 55000, 'new': 65000},
    'm34': {'base': 40000, 'new': 48000},
    'm14': {'base': 28000, 'new': 35000},
    
    # iPhone Series
    'iphone 15 pro max': {'base': 450000, 'new': 550000},
    'iphone 15 pro': {'base': 380000, 'new': 450000},
    'iphone 15 plus': {'base': 320000, 'new': 380000},
    'iphone 15': {'base': 280000, 'new': 330000},
    'iphone 14 pro max': {'base': 350000, 'new': 420000},
    'iphone 14 pro': {'base': 300000, 'new': 360000},
    'iphone 14 plus': {'base': 250000, 'new': 300000},
    'iphone 14': {'base': 220000, 'new': 260000},
    'iphone 13 pro max': {'base': 280000, 'new': 330000},
    'iphone 13 pro': {'base': 230000, 'new': 280000},
    'iphone 13': {'base': 170000, 'new': 200000},
    'iphone 13 mini': {'base': 140000, 'new': 170000},
    'iphone 12 pro max': {'base': 200000, 'new': 240000},
    'iphone 12 pro': {'base': 160000, 'new': 190000},
    'iphone 12': {'base': 120000, 'new': 145000},
    'iphone 12 mini': {'base': 95000, 'new': 115000},
    'iphone 11 pro max': {'base': 140000, 'new': 170000},
    'iphone 11 pro': {'base': 110000, 'new': 135000},
    'iphone 11': {'base': 85000, 'new': 100000},
    'iphone se 2022': {'base': 100000, 'new': 120000},
    'iphone se 2020': {'base': 65000, 'new': 80000},
    'iphone xr': {'base': 55000, 'new': 70000},
    'iphone xs max': {'base': 70000, 'new': 85000},
    'iphone xs': {'base': 55000, 'new': 70000},
    'iphone x': {'base': 45000, 'new': 55000},
    
    # Google Pixel
    'pixel 8 pro': {'base': 200000, 'new': 250000},
    'pixel 8': {'base': 150000, 'new': 180000},
    'pixel 7 pro': {'base': 140000, 'new': 170000},
    'pixel 7': {'base': 100000, 'new': 120000},
    'pixel 7a': {'base': 80000, 'new': 95000},
    'pixel 6 pro': {'base': 100000, 'new': 120000},
    'pixel 6': {'base': 70000, 'new': 85000},
    'pixel 6a': {'base': 55000, 'new': 65000},
    
    # OnePlus
    'oneplus 12': {'base': 180000, 'new': 220000},
    'oneplus 11': {'base': 130000, 'new': 160000},
    'oneplus 10 pro': {'base': 100000, 'new': 120000},
    'oneplus 10t': {'base': 85000, 'new': 100000},
    'oneplus 9 pro': {'base': 90000, 'new': 110000},
    'oneplus 9': {'base': 65000, 'new': 80000},
    'oneplus nord 3': {'base': 65000, 'new': 80000},
    'oneplus nord 2': {'base': 50000, 'new': 60000},
    'oneplus nord ce 3': {'base': 50000, 'new': 60000},
    'oneplus nord ce 2': {'base': 40000, 'new': 48000},
    
    # Xiaomi
    'xiaomi 14 ultra': {'base': 250000, 'new': 300000},
    'xiaomi 14': {'base': 180000, 'new': 220000},
    'xiaomi 13 ultra': {'base': 200000, 'new': 250000},
    'xiaomi 13 pro': {'base': 150000, 'new': 180000},
    'xiaomi 13': {'base': 110000, 'new': 130000},
    'xiaomi 12 pro': {'base': 100000, 'new': 120000},
    'xiaomi 12': {'base': 70000, 'new': 85000},
    'mi 11 ultra': {'base': 90000, 'new': 110000},
    'mi 11': {'base': 60000, 'new': 75000},
    
    # Redmi Note Series
    'redmi note 13 pro plus': {'base': 65000, 'new': 80000},
    'redmi note 13 pro': {'base': 55000, 'new': 65000},
    'redmi note 13': {'base': 40000, 'new': 48000},
    'redmi note 12 pro plus': {'base': 55000, 'new': 65000},
    'redmi note 12 pro': {'base': 45000, 'new': 55000},
    'redmi note 12': {'base': 35000, 'new': 42000},
    'redmi note 11 pro plus': {'base': 45000, 'new': 55000},
    'redmi note 11 pro': {'base': 38000, 'new': 45000},
    'redmi note 11': {'base': 28000, 'new': 35000},
    'redmi note 10 pro': {'base': 32000, 'new': 40000},
    'redmi note 10': {'base': 25000, 'new': 30000},
    
    # Poco
    'poco f5 pro': {'base': 80000, 'new': 95000},
    'poco f5': {'base': 60000, 'new': 72000},
    'poco f4': {'base': 50000, 'new': 60000},
    'poco f3': {'base': 40000, 'new': 48000},
    'poco x5 pro': {'base': 50000, 'new': 60000},
    'poco x5': {'base': 38000, 'new': 45000},
    'poco x4 pro': {'base': 40000, 'new': 48000},
    'poco m5': {'base': 25000, 'new': 30000},
    'poco m4 pro': {'base': 30000, 'new': 36000},
    
    # Oppo
    'oppo find x6 pro': {'base': 180000, 'new': 220000},
    'oppo find x5 pro': {'base': 130000, 'new': 160000},
    'oppo reno 10 pro plus': {'base': 100000, 'new': 120000},
    'oppo reno 10 pro': {'base': 80000, 'new': 95000},
    'oppo reno 10': {'base': 60000, 'new': 72000},
    'oppo reno 8 pro': {'base': 70000, 'new': 85000},
    'oppo reno 8': {'base': 55000, 'new': 65000},
    'oppo a78': {'base': 45000, 'new': 55000},
    'oppo a58': {'base': 38000, 'new': 45000},
    'oppo a38': {'base': 32000, 'new': 38000},
    'oppo a18': {'base': 28000, 'new': 33000},
    
    # Vivo
    'vivo x100 pro': {'base': 180000, 'new': 220000},
    'vivo x100': {'base': 140000, 'new': 170000},
    'vivo x90 pro': {'base': 140000, 'new': 170000},
    'vivo x90': {'base': 100000, 'new': 120000},
    'vivo v29 pro': {'base': 80000, 'new': 95000},
    'vivo v29': {'base': 65000, 'new': 78000},
    'vivo v27 pro': {'base': 70000, 'new': 85000},
    'vivo v27': {'base': 55000, 'new': 65000},
    'vivo y100': {'base': 45000, 'new': 55000},
    'vivo y36': {'base': 35000, 'new': 42000},
    'vivo y27': {'base': 32000, 'new': 38000},
    
    # Realme
    'realme gt 5 pro': {'base': 100000, 'new': 120000},
    'realme gt 3': {'base': 80000, 'new': 95000},
    'realme gt neo 5': {'base': 70000, 'new': 85000},
    'realme 11 pro plus': {'base': 60000, 'new': 72000},
    'realme 11 pro': {'base': 50000, 'new': 60000},
    'realme 11': {'base': 38000, 'new': 45000},
    'realme c55': {'base': 30000, 'new': 36000},
    'realme c53': {'base': 28000, 'new': 33000},
    'realme c33': {'base': 22000, 'new': 27000},
    'realme narzo 60 pro': {'base': 50000, 'new': 60000},
    'realme narzo 60': {'base': 38000, 'new': 45000},
    
    # Tecno
    'tecno phantom x2 pro': {'base': 100000, 'new': 120000},
    'tecno phantom x2': {'base': 75000, 'new': 90000},
    'tecno camon 20 pro': {'base': 50000, 'new': 60000},
    'tecno camon 20': {'base': 40000, 'new': 48000},
    'tecno spark 20 pro': {'base': 35000, 'new': 42000},
    'tecno spark 20': {'base': 28000, 'new': 33000},
    'tecno spark 10 pro': {'base': 30000, 'new': 36000},
    'tecno spark 10': {'base': 22000, 'new': 27000},
    'tecno pova 5 pro': {'base': 42000, 'new': 50000},
    'tecno pova 5': {'base': 35000, 'new': 42000},
    
    # Infinix
    'infinix zero 30': {'base': 55000, 'new': 65000},
    'infinix note 30 pro': {'base': 45000, 'new': 55000},
    'infinix note 30': {'base': 38000, 'new': 45000},
    'infinix hot 30': {'base': 28000, 'new': 33000},
    'infinix smart 8': {'base': 22000, 'new': 27000},
    
    # Huawei
    'huawei mate 60 pro': {'base': 300000, 'new': 380000},
    'huawei p60 pro': {'base': 250000, 'new': 300000},
    'huawei nova 11 pro': {'base': 100000, 'new': 120000},
    'huawei nova 11': {'base': 75000, 'new': 90000},
    
    # Nokia
    'nokia g42': {'base': 38000, 'new': 45000},
    'nokia g22': {'base': 30000, 'new': 36000},
    'nokia c32': {'base': 22000, 'new': 27000},
}


def get_mobile_market_price(title: str, condition: str = 'used') -> Optional[float]:
    """
    Get realistic market price based on model name
    Returns None if model not found in price database
    """
    title_lower = title.lower()
    
    # Try to find exact or partial match
    best_match = None
    best_match_len = 0
    
    for model_key, prices in MOBILE_MARKET_PRICES.items():
        # Check if model name is in title
        if model_key in title_lower:
            # Prefer longer matches (more specific)
            if len(model_key) > best_match_len:
                best_match = prices
                best_match_len = len(model_key)
    
    if best_match:
        if condition.lower() == 'new':
            return best_match['new']
        else:
            return best_match['base']
    
    return None


def apply_mobile_price_adjustments(base_price: float, data: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Apply realistic price adjustments based on PTA, warranty, box, condition, etc.
    Returns adjusted price and list of adjustments made
    """
    adjustments = []
    final_price = base_price
    
    condition = data.get('condition', 'used').lower()
    
    # PTA Status - MAJOR impact in Pakistan
    has_pta = data.get('has_pta', False)
    if has_pta:
        # PTA approved phones are worth 15-25% more
        pta_bonus = base_price * 0.18
        final_price += pta_bonus
        adjustments.append(f"+Rs.{int(pta_bonus):,} (PTA Approved)")
    else:
        # Non-PTA phones have significant penalty
        pta_penalty = base_price * 0.15
        final_price -= pta_penalty
        adjustments.append(f"-Rs.{int(pta_penalty):,} (Non-PTA)")
    
    # Warranty - Important for resale
    has_warranty = data.get('has_warranty', False)
    if has_warranty:
        warranty_bonus = base_price * 0.08
        final_price += warranty_bonus
        adjustments.append(f"+Rs.{int(warranty_bonus):,} (With Warranty)")
    
    # Original Box & Accessories
    has_box = data.get('has_box', False)
    if has_box:
        box_bonus = base_price * 0.05
        final_price += box_bonus
        adjustments.append(f"+Rs.{int(box_bonus):,} (Original Box)")
    
    # Condition adjustments (if not already factored in base price)
    if condition == 'new':
        # Already using 'new' price from database
        pass
    elif condition == 'refurbished':
        refurb_penalty = base_price * 0.10
        final_price -= refurb_penalty
        adjustments.append(f"-Rs.{int(refurb_penalty):,} (Refurbished)")
    elif condition in ['used', 'excellent']:
        # Minor discount for used condition
        pass
    elif condition == 'good':
        good_penalty = base_price * 0.05
        final_price -= good_penalty
        adjustments.append(f"-Rs.{int(good_penalty):,} (Good condition)")
    elif condition == 'fair':
        fair_penalty = base_price * 0.12
        final_price -= fair_penalty
        adjustments.append(f"-Rs.{int(fair_penalty):,} (Fair condition)")
    
    # RAM adjustment (if specified and not 0)
    ram = data.get('ram', 0)
    if ram > 0:
        if ram >= 12:
            ram_bonus = base_price * 0.05
            final_price += ram_bonus
            adjustments.append(f"+Rs.{int(ram_bonus):,} ({ram}GB RAM)")
        elif ram <= 4:
            ram_penalty = base_price * 0.05
            final_price -= ram_penalty
            adjustments.append(f"-Rs.{int(ram_penalty):,} ({ram}GB RAM)")
    
    # Storage adjustment (if specified and not 0)
    storage = data.get('storage', 0)
    if storage > 0:
        if storage >= 512:
            storage_bonus = base_price * 0.08
            final_price += storage_bonus
            adjustments.append(f"+Rs.{int(storage_bonus):,} ({storage}GB Storage)")
        elif storage >= 256:
            storage_bonus = base_price * 0.03
            final_price += storage_bonus
            adjustments.append(f"+Rs.{int(storage_bonus):,} ({storage}GB Storage)")
        elif storage <= 64:
            storage_penalty = base_price * 0.05
            final_price -= storage_penalty
            adjustments.append(f"-Rs.{int(storage_penalty):,} ({storage}GB Storage)")
    
    return final_price, adjustments


# Realistic laptop market prices for Pakistani market (December 2024)
LAPTOP_MARKET_PRICES = {
    # Dell Inspiron Series
    'inspiron 15 3520': {'base': 85000, 'new': 105000, 'tier': 'budget'},
    'inspiron 15 3521': {'base': 90000, 'new': 110000, 'tier': 'budget'},
    'inspiron 15 3525': {'base': 95000, 'new': 115000, 'tier': 'budget'},
    'inspiron 15 5510': {'base': 110000, 'new': 135000, 'tier': 'mid'},
    'inspiron 15 5520': {'base': 120000, 'new': 145000, 'tier': 'mid'},
    'inspiron 15 5530': {'base': 130000, 'new': 155000, 'tier': 'mid'},
    'inspiron 14 5420': {'base': 115000, 'new': 140000, 'tier': 'mid'},
    'inspiron 14 5430': {'base': 125000, 'new': 150000, 'tier': 'mid'},
    'inspiron 16 5620': {'base': 135000, 'new': 160000, 'tier': 'mid'},
    'inspiron 16 5630': {'base': 145000, 'new': 170000, 'tier': 'mid'},
    'inspiron 7420': {'base': 140000, 'new': 165000, 'tier': 'mid'},
    'inspiron 7430': {'base': 150000, 'new': 175000, 'tier': 'mid'},
    
    # Dell XPS Series (Premium)
    'xps 13': {'base': 180000, 'new': 220000, 'tier': 'premium'},
    'xps 13 plus': {'base': 220000, 'new': 270000, 'tier': 'premium'},
    'xps 13 9310': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'xps 13 9315': {'base': 190000, 'new': 230000, 'tier': 'premium'},
    'xps 13 9320': {'base': 210000, 'new': 250000, 'tier': 'premium'},
    'xps 15': {'base': 250000, 'new': 300000, 'tier': 'premium'},
    'xps 15 9510': {'base': 230000, 'new': 280000, 'tier': 'premium'},
    'xps 15 9520': {'base': 260000, 'new': 310000, 'tier': 'premium'},
    'xps 15 9530': {'base': 280000, 'new': 330000, 'tier': 'premium'},
    'xps 17': {'base': 320000, 'new': 380000, 'tier': 'premium'},
    'xps 17 9710': {'base': 300000, 'new': 350000, 'tier': 'premium'},
    'xps 17 9720': {'base': 340000, 'new': 400000, 'tier': 'premium'},
    
    # Dell Latitude (Business)
    'latitude 3420': {'base': 95000, 'new': 115000, 'tier': 'business'},
    'latitude 3520': {'base': 100000, 'new': 120000, 'tier': 'business'},
    'latitude 5420': {'base': 130000, 'new': 155000, 'tier': 'business'},
    'latitude 5520': {'base': 140000, 'new': 165000, 'tier': 'business'},
    'latitude 5530': {'base': 150000, 'new': 175000, 'tier': 'business'},
    'latitude 7420': {'base': 160000, 'new': 190000, 'tier': 'business'},
    'latitude 7520': {'base': 175000, 'new': 205000, 'tier': 'business'},
    'latitude 7530': {'base': 185000, 'new': 215000, 'tier': 'business'},
    'latitude 9420': {'base': 200000, 'new': 240000, 'tier': 'business'},
    'latitude 9520': {'base': 220000, 'new': 260000, 'tier': 'business'},
    
    # Dell Vostro (Business)
    'vostro 3420': {'base': 80000, 'new': 95000, 'tier': 'budget'},
    'vostro 3520': {'base': 85000, 'new': 100000, 'tier': 'budget'},
    'vostro 5410': {'base': 100000, 'new': 120000, 'tier': 'mid'},
    'vostro 5510': {'base': 110000, 'new': 130000, 'tier': 'mid'},
    'vostro 5620': {'base': 120000, 'new': 140000, 'tier': 'mid'},
    
    # Dell G Series (Gaming)
    'g15 5510': {'base': 130000, 'new': 155000, 'tier': 'gaming'},
    'g15 5520': {'base': 145000, 'new': 170000, 'tier': 'gaming'},
    'g15 5530': {'base': 160000, 'new': 185000, 'tier': 'gaming'},
    'g16 7620': {'base': 180000, 'new': 210000, 'tier': 'gaming'},
    'g16 7630': {'base': 200000, 'new': 235000, 'tier': 'gaming'},
    
    # Dell Alienware (Gaming Premium)
    'alienware m15': {'base': 250000, 'new': 300000, 'tier': 'gaming_premium'},
    'alienware m15 r7': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'alienware m16': {'base': 300000, 'new': 360000, 'tier': 'gaming_premium'},
    'alienware m17': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'alienware m18': {'base': 400000, 'new': 480000, 'tier': 'gaming_premium'},
    'alienware x14': {'base': 280000, 'new': 340000, 'tier': 'gaming_premium'},
    'alienware x15': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'alienware x17': {'base': 380000, 'new': 450000, 'tier': 'gaming_premium'},
    
    # HP Pavilion Series
    'pavilion 14': {'base': 85000, 'new': 100000, 'tier': 'budget'},
    'pavilion 15': {'base': 90000, 'new': 105000, 'tier': 'budget'},
    'pavilion 15-eg': {'base': 95000, 'new': 115000, 'tier': 'budget'},
    'pavilion 15-eh': {'base': 90000, 'new': 110000, 'tier': 'budget'},
    'pavilion x360': {'base': 110000, 'new': 130000, 'tier': 'mid'},
    'pavilion x360 14': {'base': 115000, 'new': 135000, 'tier': 'mid'},
    'pavilion plus': {'base': 130000, 'new': 155000, 'tier': 'mid'},
    'pavilion aero': {'base': 120000, 'new': 145000, 'tier': 'mid'},
    
    # HP Envy Series
    'envy 13': {'base': 140000, 'new': 165000, 'tier': 'premium'},
    'envy 14': {'base': 150000, 'new': 175000, 'tier': 'premium'},
    'envy 15': {'base': 160000, 'new': 190000, 'tier': 'premium'},
    'envy 16': {'base': 180000, 'new': 210000, 'tier': 'premium'},
    'envy x360': {'base': 145000, 'new': 170000, 'tier': 'premium'},
    'envy x360 13': {'base': 150000, 'new': 175000, 'tier': 'premium'},
    'envy x360 15': {'base': 165000, 'new': 195000, 'tier': 'premium'},
    
    # HP Spectre Series (Ultra Premium)
    'spectre x360': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'spectre x360 13': {'base': 230000, 'new': 270000, 'tier': 'premium'},
    'spectre x360 14': {'base': 250000, 'new': 295000, 'tier': 'premium'},
    'spectre x360 16': {'base': 280000, 'new': 330000, 'tier': 'premium'},
    
    # HP EliteBook (Business)
    'elitebook 830': {'base': 150000, 'new': 175000, 'tier': 'business'},
    'elitebook 840': {'base': 160000, 'new': 190000, 'tier': 'business'},
    'elitebook 850': {'base': 170000, 'new': 200000, 'tier': 'business'},
    'elitebook 860': {'base': 180000, 'new': 210000, 'tier': 'business'},
    'elitebook x360': {'base': 175000, 'new': 205000, 'tier': 'business'},
    'elitebook 1030': {'base': 200000, 'new': 240000, 'tier': 'business'},
    'elitebook 1040': {'base': 220000, 'new': 260000, 'tier': 'business'},
    
    # HP ProBook (Business Budget)
    'probook 430': {'base': 95000, 'new': 115000, 'tier': 'business'},
    'probook 440': {'base': 100000, 'new': 120000, 'tier': 'business'},
    'probook 450': {'base': 105000, 'new': 125000, 'tier': 'business'},
    'probook 455': {'base': 110000, 'new': 130000, 'tier': 'business'},
    'probook 640': {'base': 120000, 'new': 140000, 'tier': 'business'},
    'probook 650': {'base': 130000, 'new': 150000, 'tier': 'business'},
    
    # HP Omen (Gaming)
    'omen 15': {'base': 180000, 'new': 210000, 'tier': 'gaming'},
    'omen 16': {'base': 200000, 'new': 235000, 'tier': 'gaming'},
    'omen 17': {'base': 230000, 'new': 270000, 'tier': 'gaming'},
    'omen transcend': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    
    # HP Victus (Gaming Budget)
    'victus 15': {'base': 130000, 'new': 155000, 'tier': 'gaming'},
    'victus 16': {'base': 150000, 'new': 175000, 'tier': 'gaming'},
    
    # HP ZBook (Workstation)
    'zbook firefly': {'base': 180000, 'new': 210000, 'tier': 'workstation'},
    'zbook power': {'base': 200000, 'new': 240000, 'tier': 'workstation'},
    'zbook studio': {'base': 280000, 'new': 330000, 'tier': 'workstation'},
    'zbook fury': {'base': 350000, 'new': 420000, 'tier': 'workstation'},
    
    # Lenovo IdeaPad Series
    'ideapad 1': {'base': 55000, 'new': 65000, 'tier': 'entry'},
    'ideapad 3': {'base': 70000, 'new': 85000, 'tier': 'budget'},
    'ideapad 3i': {'base': 75000, 'new': 90000, 'tier': 'budget'},
    'ideapad 5': {'base': 95000, 'new': 115000, 'tier': 'mid'},
    'ideapad 5i': {'base': 100000, 'new': 120000, 'tier': 'mid'},
    'ideapad 5 pro': {'base': 120000, 'new': 145000, 'tier': 'mid'},
    'ideapad slim 3': {'base': 80000, 'new': 95000, 'tier': 'budget'},
    'ideapad slim 5': {'base': 105000, 'new': 125000, 'tier': 'mid'},
    'ideapad slim 7': {'base': 140000, 'new': 165000, 'tier': 'premium'},
    'ideapad flex 5': {'base': 110000, 'new': 130000, 'tier': 'mid'},
    'ideapad gaming 3': {'base': 110000, 'new': 130000, 'tier': 'gaming'},
    'ideapad gaming 3i': {'base': 115000, 'new': 135000, 'tier': 'gaming'},
    
    # Lenovo ThinkPad Series (Business Premium)
    'thinkpad e14': {'base': 110000, 'new': 130000, 'tier': 'business'},
    'thinkpad e15': {'base': 115000, 'new': 135000, 'tier': 'business'},
    'thinkpad e16': {'base': 120000, 'new': 140000, 'tier': 'business'},
    'thinkpad l14': {'base': 130000, 'new': 155000, 'tier': 'business'},
    'thinkpad l15': {'base': 135000, 'new': 160000, 'tier': 'business'},
    'thinkpad t14': {'base': 160000, 'new': 190000, 'tier': 'business'},
    'thinkpad t14s': {'base': 175000, 'new': 205000, 'tier': 'business'},
    'thinkpad t15': {'base': 170000, 'new': 200000, 'tier': 'business'},
    'thinkpad t16': {'base': 180000, 'new': 210000, 'tier': 'business'},
    'thinkpad x1 carbon': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'thinkpad x1 yoga': {'base': 230000, 'new': 270000, 'tier': 'premium'},
    'thinkpad x1 nano': {'base': 210000, 'new': 250000, 'tier': 'premium'},
    'thinkpad x13': {'base': 165000, 'new': 195000, 'tier': 'business'},
    'thinkpad p14s': {'base': 190000, 'new': 225000, 'tier': 'workstation'},
    'thinkpad p15': {'base': 250000, 'new': 300000, 'tier': 'workstation'},
    'thinkpad p16': {'base': 280000, 'new': 330000, 'tier': 'workstation'},
    
    # Lenovo ThinkBook (Business Budget)
    'thinkbook 14': {'base': 100000, 'new': 120000, 'tier': 'business'},
    'thinkbook 15': {'base': 105000, 'new': 125000, 'tier': 'business'},
    'thinkbook 16': {'base': 115000, 'new': 135000, 'tier': 'business'},
    'thinkbook 14s': {'base': 120000, 'new': 140000, 'tier': 'business'},
    'thinkbook plus': {'base': 180000, 'new': 210000, 'tier': 'premium'},
    
    # Lenovo Yoga Series (Premium 2-in-1)
    'yoga 6': {'base': 120000, 'new': 145000, 'tier': 'premium'},
    'yoga 7': {'base': 140000, 'new': 165000, 'tier': 'premium'},
    'yoga 7i': {'base': 145000, 'new': 170000, 'tier': 'premium'},
    'yoga 9i': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'yoga slim 7': {'base': 150000, 'new': 180000, 'tier': 'premium'},
    'yoga slim 7 pro': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'yoga slim 9i': {'base': 230000, 'new': 270000, 'tier': 'premium'},
    
    # Lenovo Legion (Gaming)
    'legion 5': {'base': 160000, 'new': 190000, 'tier': 'gaming'},
    'legion 5i': {'base': 170000, 'new': 200000, 'tier': 'gaming'},
    'legion 5 pro': {'base': 200000, 'new': 235000, 'tier': 'gaming'},
    'legion 5i pro': {'base': 220000, 'new': 260000, 'tier': 'gaming'},
    'legion 7': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'legion 7i': {'base': 300000, 'new': 350000, 'tier': 'gaming_premium'},
    'legion slim 5': {'base': 180000, 'new': 210000, 'tier': 'gaming'},
    'legion slim 7': {'base': 250000, 'new': 300000, 'tier': 'gaming_premium'},
    'legion pro 5': {'base': 240000, 'new': 285000, 'tier': 'gaming'},
    'legion pro 7': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    
    # Lenovo LOQ (Gaming Budget)
    'loq 15': {'base': 120000, 'new': 145000, 'tier': 'gaming'},
    'loq 16': {'base': 135000, 'new': 160000, 'tier': 'gaming'},
    
    # Apple MacBook Series
    'macbook air m1': {'base': 150000, 'new': 180000, 'tier': 'premium'},
    'macbook air m2': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'macbook air m3': {'base': 240000, 'new': 290000, 'tier': 'premium'},
    'macbook air 13': {'base': 180000, 'new': 220000, 'tier': 'premium'},
    'macbook air 15': {'base': 230000, 'new': 280000, 'tier': 'premium'},
    'macbook pro 13': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'macbook pro 13 m1': {'base': 180000, 'new': 210000, 'tier': 'premium'},
    'macbook pro 13 m2': {'base': 230000, 'new': 270000, 'tier': 'premium'},
    'macbook pro 14': {'base': 350000, 'new': 420000, 'tier': 'premium'},
    'macbook pro 14 m3': {'base': 380000, 'new': 450000, 'tier': 'premium'},
    'macbook pro 14 m3 pro': {'base': 450000, 'new': 530000, 'tier': 'premium'},
    'macbook pro 14 m3 max': {'base': 600000, 'new': 700000, 'tier': 'premium'},
    'macbook pro 16': {'base': 420000, 'new': 500000, 'tier': 'premium'},
    'macbook pro 16 m3 pro': {'base': 550000, 'new': 650000, 'tier': 'premium'},
    'macbook pro 16 m3 max': {'base': 750000, 'new': 880000, 'tier': 'premium'},
    
    # ASUS VivoBook Series
    'vivobook 14': {'base': 75000, 'new': 90000, 'tier': 'budget'},
    'vivobook 15': {'base': 80000, 'new': 95000, 'tier': 'budget'},
    'vivobook 16': {'base': 90000, 'new': 110000, 'tier': 'budget'},
    'vivobook s14': {'base': 100000, 'new': 120000, 'tier': 'mid'},
    'vivobook s15': {'base': 110000, 'new': 130000, 'tier': 'mid'},
    'vivobook pro': {'base': 130000, 'new': 155000, 'tier': 'mid'},
    'vivobook pro 14': {'base': 135000, 'new': 160000, 'tier': 'mid'},
    'vivobook pro 15': {'base': 145000, 'new': 170000, 'tier': 'mid'},
    'vivobook flip': {'base': 95000, 'new': 115000, 'tier': 'mid'},
    
    # ASUS ZenBook Series (Premium)
    'zenbook 13': {'base': 150000, 'new': 180000, 'tier': 'premium'},
    'zenbook 14': {'base': 160000, 'new': 190000, 'tier': 'premium'},
    'zenbook 14 oled': {'base': 180000, 'new': 210000, 'tier': 'premium'},
    'zenbook 15': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'zenbook pro': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'zenbook pro 14': {'base': 210000, 'new': 250000, 'tier': 'premium'},
    'zenbook pro 15': {'base': 230000, 'new': 270000, 'tier': 'premium'},
    'zenbook duo': {'base': 250000, 'new': 300000, 'tier': 'premium'},
    'zenbook s13': {'base': 190000, 'new': 225000, 'tier': 'premium'},
    'zenbook flip': {'base': 175000, 'new': 205000, 'tier': 'premium'},
    
    # ASUS ROG (Gaming)
    'rog strix g15': {'base': 180000, 'new': 210000, 'tier': 'gaming'},
    'rog strix g16': {'base': 200000, 'new': 235000, 'tier': 'gaming'},
    'rog strix g17': {'base': 220000, 'new': 260000, 'tier': 'gaming'},
    'rog strix g18': {'base': 250000, 'new': 295000, 'tier': 'gaming'},
    'rog strix scar': {'base': 300000, 'new': 360000, 'tier': 'gaming_premium'},
    'rog strix scar 15': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'rog strix scar 16': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'rog strix scar 17': {'base': 350000, 'new': 420000, 'tier': 'gaming_premium'},
    'rog strix scar 18': {'base': 400000, 'new': 480000, 'tier': 'gaming_premium'},
    'rog zephyrus g14': {'base': 220000, 'new': 260000, 'tier': 'gaming'},
    'rog zephyrus g15': {'base': 250000, 'new': 300000, 'tier': 'gaming'},
    'rog zephyrus g16': {'base': 280000, 'new': 330000, 'tier': 'gaming'},
    'rog zephyrus m16': {'base': 300000, 'new': 360000, 'tier': 'gaming_premium'},
    'rog zephyrus duo': {'base': 400000, 'new': 480000, 'tier': 'gaming_premium'},
    'rog flow x13': {'base': 200000, 'new': 240000, 'tier': 'gaming'},
    'rog flow x16': {'base': 280000, 'new': 330000, 'tier': 'gaming'},
    'rog flow z13': {'base': 250000, 'new': 300000, 'tier': 'gaming'},
    
    # ASUS TUF (Gaming Budget)
    'tuf gaming a15': {'base': 130000, 'new': 155000, 'tier': 'gaming'},
    'tuf gaming a16': {'base': 145000, 'new': 170000, 'tier': 'gaming'},
    'tuf gaming a17': {'base': 150000, 'new': 175000, 'tier': 'gaming'},
    'tuf gaming f15': {'base': 135000, 'new': 160000, 'tier': 'gaming'},
    'tuf gaming f16': {'base': 150000, 'new': 175000, 'tier': 'gaming'},
    'tuf gaming f17': {'base': 160000, 'new': 185000, 'tier': 'gaming'},
    'tuf dash f15': {'base': 140000, 'new': 165000, 'tier': 'gaming'},
    
    # ASUS ExpertBook (Business)
    'expertbook b1': {'base': 100000, 'new': 120000, 'tier': 'business'},
    'expertbook b5': {'base': 140000, 'new': 165000, 'tier': 'business'},
    'expertbook b9': {'base': 200000, 'new': 240000, 'tier': 'business'},
    
    # Acer Aspire Series
    'aspire 3': {'base': 60000, 'new': 75000, 'tier': 'entry'},
    'aspire 5': {'base': 80000, 'new': 95000, 'tier': 'budget'},
    'aspire 7': {'base': 100000, 'new': 120000, 'tier': 'mid'},
    'aspire vero': {'base': 95000, 'new': 115000, 'tier': 'mid'},
    
    # Acer Swift Series (Premium)
    'swift 3': {'base': 95000, 'new': 115000, 'tier': 'mid'},
    'swift 5': {'base': 140000, 'new': 165000, 'tier': 'premium'},
    'swift x': {'base': 150000, 'new': 180000, 'tier': 'premium'},
    'swift go': {'base': 110000, 'new': 130000, 'tier': 'mid'},
    'swift edge': {'base': 160000, 'new': 190000, 'tier': 'premium'},
    
    # Acer Spin (2-in-1)
    'spin 3': {'base': 85000, 'new': 100000, 'tier': 'mid'},
    'spin 5': {'base': 130000, 'new': 155000, 'tier': 'premium'},
    
    # Acer Nitro (Gaming)
    'nitro 5': {'base': 120000, 'new': 145000, 'tier': 'gaming'},
    'nitro 16': {'base': 150000, 'new': 180000, 'tier': 'gaming'},
    'nitro 17': {'base': 160000, 'new': 190000, 'tier': 'gaming'},
    'nitro v': {'base': 110000, 'new': 130000, 'tier': 'gaming'},
    
    # Acer Predator (Gaming Premium)
    'predator helios 300': {'base': 200000, 'new': 240000, 'tier': 'gaming'},
    'predator helios 16': {'base': 250000, 'new': 300000, 'tier': 'gaming_premium'},
    'predator helios 18': {'base': 300000, 'new': 360000, 'tier': 'gaming_premium'},
    'predator triton 300': {'base': 220000, 'new': 260000, 'tier': 'gaming'},
    'predator triton 500': {'base': 300000, 'new': 360000, 'tier': 'gaming_premium'},
    'predator triton 16': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'predator triton 17': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    
    # MSI Gaming Laptops
    'msi gf63': {'base': 110000, 'new': 130000, 'tier': 'gaming'},
    'msi gf65': {'base': 120000, 'new': 145000, 'tier': 'gaming'},
    'msi gf76': {'base': 140000, 'new': 165000, 'tier': 'gaming'},
    'msi katana 15': {'base': 140000, 'new': 165000, 'tier': 'gaming'},
    'msi katana 17': {'base': 160000, 'new': 190000, 'tier': 'gaming'},
    'msi cyborg 15': {'base': 130000, 'new': 155000, 'tier': 'gaming'},
    'msi thin gf63': {'base': 115000, 'new': 135000, 'tier': 'gaming'},
    'msi pulse 15': {'base': 170000, 'new': 200000, 'tier': 'gaming'},
    'msi pulse 17': {'base': 190000, 'new': 225000, 'tier': 'gaming'},
    'msi crosshair 15': {'base': 200000, 'new': 240000, 'tier': 'gaming'},
    'msi crosshair 16': {'base': 230000, 'new': 270000, 'tier': 'gaming'},
    'msi vector gp66': {'base': 220000, 'new': 260000, 'tier': 'gaming'},
    'msi vector gp76': {'base': 250000, 'new': 300000, 'tier': 'gaming'},
    'msi raider ge66': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'msi raider ge76': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'msi raider ge78': {'base': 380000, 'new': 450000, 'tier': 'gaming_premium'},
    'msi stealth 14': {'base': 200000, 'new': 240000, 'tier': 'gaming'},
    'msi stealth 15': {'base': 250000, 'new': 300000, 'tier': 'gaming_premium'},
    'msi stealth 16': {'base': 280000, 'new': 330000, 'tier': 'gaming_premium'},
    'msi stealth 17': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'msi titan gt77': {'base': 500000, 'new': 600000, 'tier': 'gaming_premium'},
    'msi titan 18': {'base': 550000, 'new': 660000, 'tier': 'gaming_premium'},
    
    # MSI Creator/Business
    'msi modern 14': {'base': 90000, 'new': 110000, 'tier': 'mid'},
    'msi modern 15': {'base': 100000, 'new': 120000, 'tier': 'mid'},
    'msi prestige 14': {'base': 150000, 'new': 180000, 'tier': 'premium'},
    'msi prestige 15': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'msi prestige 16': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'msi creator z16': {'base': 280000, 'new': 330000, 'tier': 'workstation'},
    'msi creator z17': {'base': 320000, 'new': 380000, 'tier': 'workstation'},
    
    # Razer Gaming
    'razer blade 14': {'base': 280000, 'new': 340000, 'tier': 'gaming_premium'},
    'razer blade 15': {'base': 320000, 'new': 380000, 'tier': 'gaming_premium'},
    'razer blade 16': {'base': 380000, 'new': 450000, 'tier': 'gaming_premium'},
    'razer blade 17': {'base': 400000, 'new': 480000, 'tier': 'gaming_premium'},
    'razer blade 18': {'base': 450000, 'new': 540000, 'tier': 'gaming_premium'},
    'razer blade stealth': {'base': 200000, 'new': 240000, 'tier': 'gaming'},
    
    # Microsoft Surface
    'surface laptop 5': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'surface laptop go': {'base': 130000, 'new': 155000, 'tier': 'mid'},
    'surface laptop go 2': {'base': 140000, 'new': 165000, 'tier': 'mid'},
    'surface laptop go 3': {'base': 160000, 'new': 190000, 'tier': 'mid'},
    'surface laptop studio': {'base': 280000, 'new': 330000, 'tier': 'premium'},
    'surface laptop studio 2': {'base': 320000, 'new': 380000, 'tier': 'premium'},
    'surface pro 8': {'base': 180000, 'new': 215000, 'tier': 'premium'},
    'surface pro 9': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'surface book 3': {'base': 250000, 'new': 300000, 'tier': 'premium'},
    
    # Samsung Galaxy Book
    'galaxy book 2': {'base': 130000, 'new': 155000, 'tier': 'mid'},
    'galaxy book 2 pro': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'galaxy book 2 pro 360': {'base': 190000, 'new': 225000, 'tier': 'premium'},
    'galaxy book 3': {'base': 150000, 'new': 180000, 'tier': 'mid'},
    'galaxy book 3 pro': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'galaxy book 3 pro 360': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'galaxy book 3 ultra': {'base': 300000, 'new': 360000, 'tier': 'premium'},
    
    # LG Gram
    'lg gram 14': {'base': 170000, 'new': 200000, 'tier': 'premium'},
    'lg gram 15': {'base': 180000, 'new': 215000, 'tier': 'premium'},
    'lg gram 16': {'base': 200000, 'new': 240000, 'tier': 'premium'},
    'lg gram 17': {'base': 220000, 'new': 260000, 'tier': 'premium'},
    'lg gram style': {'base': 250000, 'new': 300000, 'tier': 'premium'},
    
    # Generic processor-based pricing (fallback)
    'i3': {'base': 55000, 'new': 70000, 'tier': 'entry'},
    'i5': {'base': 80000, 'new': 100000, 'tier': 'budget'},
    'i7': {'base': 120000, 'new': 150000, 'tier': 'mid'},
    'i9': {'base': 180000, 'new': 220000, 'tier': 'premium'},
    'ryzen 3': {'base': 50000, 'new': 65000, 'tier': 'entry'},
    'ryzen 5': {'base': 75000, 'new': 95000, 'tier': 'budget'},
    'ryzen 7': {'base': 110000, 'new': 140000, 'tier': 'mid'},
    'ryzen 9': {'base': 170000, 'new': 210000, 'tier': 'premium'},
}


def get_laptop_market_price(title: str, condition: str = 'used') -> Tuple[Optional[float], Optional[str]]:
    """
    Get realistic market price based on laptop model name
    Returns (price, tier) or (None, None) if not found
    """
    title_lower = title.lower()
    
    # Try to find exact or partial match
    best_match = None
    best_match_len = 0
    best_tier = None
    
    for model_key, prices in LAPTOP_MARKET_PRICES.items():
        # Check if model name is in title
        if model_key in title_lower:
            # Prefer longer matches (more specific)
            if len(model_key) > best_match_len:
                best_match = prices
                best_match_len = len(model_key)
                best_tier = prices.get('tier', 'mid')
    
    if best_match:
        if condition.lower() == 'new':
            return best_match['new'], best_tier
        else:
            return best_match['base'], best_tier
    
    return None, None


def apply_laptop_price_adjustments(base_price: float, data: Dict[str, Any], tier: str = 'mid') -> Tuple[float, List[str]]:
    """
    Apply realistic price adjustments for laptops based on specs and condition
    Returns adjusted price and list of adjustments made
    """
    adjustments = []
    final_price = base_price
    
    condition = data.get('condition', 'used').lower()
    
    # Condition adjustments
    if condition == 'new':
        pass  # Already using 'new' price
    elif condition == 'refurbished':
        refurb_penalty = base_price * 0.12
        final_price -= refurb_penalty
        adjustments.append(f"-Rs.{int(refurb_penalty):,} (Refurbished)")
    elif condition == 'used':
        pass  # Already using 'base' price
    elif condition == 'excellent':
        excellent_bonus = base_price * 0.05
        final_price += excellent_bonus
        adjustments.append(f"+Rs.{int(excellent_bonus):,} (Excellent condition)")
    elif condition == 'good':
        good_penalty = base_price * 0.05
        final_price -= good_penalty
        adjustments.append(f"-Rs.{int(good_penalty):,} (Good condition)")
    elif condition == 'fair':
        fair_penalty = base_price * 0.15
        final_price -= fair_penalty
        adjustments.append(f"-Rs.{int(fair_penalty):,} (Fair condition)")
    
    # Warranty impact
    has_warranty = data.get('has_warranty', False)
    if has_warranty:
        warranty_bonus = base_price * 0.08
        final_price += warranty_bonus
        adjustments.append(f"+Rs.{int(warranty_bonus):,} (With Warranty)")
    
    # SSD bonus
    has_ssd = data.get('has_ssd', False)
    if has_ssd:
        ssd_bonus = base_price * 0.05
        final_price += ssd_bonus
        adjustments.append(f"+Rs.{int(ssd_bonus):,} (SSD Storage)")
    
    # RAM adjustments - handle both numeric and string inputs
    ram_raw = data.get('ram', 0)
    ram = 0
    if isinstance(ram_raw, (int, float)):
        ram = int(ram_raw)
    elif isinstance(ram_raw, str):
        # Extract number from strings like "16gb", "16 GB", "16"
        import re
        ram_match = re.search(r'(\d+)', ram_raw)
        if ram_match:
            ram = int(ram_match.group(1))
    
    if ram > 0:
        if ram >= 32:
            ram_bonus = base_price * 0.12
            final_price += ram_bonus
            adjustments.append(f"+Rs.{int(ram_bonus):,} ({ram}GB RAM)")
        elif ram >= 16:
            ram_bonus = base_price * 0.05
            final_price += ram_bonus
            adjustments.append(f"+Rs.{int(ram_bonus):,} ({ram}GB RAM)")
        elif ram <= 4:
            ram_penalty = base_price * 0.10
            final_price -= ram_penalty
            adjustments.append(f"-Rs.{int(ram_penalty):,} ({ram}GB RAM)")
    
    # Storage adjustments - handle both numeric and string inputs
    storage_raw = data.get('storage', 0)
    storage = 0
    if isinstance(storage_raw, (int, float)):
        storage = int(storage_raw)
    elif isinstance(storage_raw, str):
        # Extract number from strings like "512gb", "1tb", "256 GB"
        import re
        storage_str = storage_raw.lower()
        if 'tb' in storage_str:
            tb_match = re.search(r'(\d+)', storage_str)
            if tb_match:
                storage = int(tb_match.group(1)) * 1000  # Convert TB to GB
        else:
            gb_match = re.search(r'(\d+)', storage_str)
            if gb_match:
                storage = int(gb_match.group(1))
    
    if storage > 0:
        if storage >= 1000:  # 1TB+
            storage_bonus = base_price * 0.08
            final_price += storage_bonus
            adjustments.append(f"+Rs.{int(storage_bonus):,} ({storage}GB Storage)")
        elif storage >= 512:
            storage_bonus = base_price * 0.03
            final_price += storage_bonus
            adjustments.append(f"+Rs.{int(storage_bonus):,} ({storage}GB Storage)")
        elif storage <= 128:
            storage_penalty = base_price * 0.08
            final_price -= storage_penalty
            adjustments.append(f"-Rs.{int(storage_penalty):,} ({storage}GB Storage)")
    
    # Gaming laptop bonus (dedicated GPU)
    is_gaming = data.get('is_gaming', False)
    if is_gaming and tier not in ['gaming', 'gaming_premium']:
        gaming_bonus = base_price * 0.10
        final_price += gaming_bonus
        adjustments.append(f"+Rs.{int(gaming_bonus):,} (Gaming/GPU)")
    
    # Touchscreen bonus
    is_touchscreen = data.get('is_touchscreen', False)
    if is_touchscreen:
        touch_bonus = base_price * 0.05
        final_price += touch_bonus
        adjustments.append(f"+Rs.{int(touch_bonus):,} (Touchscreen)")
    
    # Processor generation bonus (if mentioned)
    title = data.get('title', '').lower()
    description = data.get('description', '').lower()
    text = f"{title} {description}"
    
    # Check for latest generation processors
    if any(x in text for x in ['13th gen', '14th gen', '13900', '14900', '13700', '14700', '7945', '7940']):
        gen_bonus = base_price * 0.10
        final_price += gen_bonus
        adjustments.append(f"+Rs.{int(gen_bonus):,} (Latest Gen Processor)")
    elif any(x in text for x in ['12th gen', '12900', '12700', '6900', '6800']):
        gen_bonus = base_price * 0.05
        final_price += gen_bonus
        adjustments.append(f"+Rs.{int(gen_bonus):,} (Recent Gen Processor)")
    
    # GPU bonus for specific models (from dropdown or text)
    gpu = data.get('gpu', '').lower()
    gpu_applied = False
    
    # Check dropdown GPU values first (most reliable)
    if 'rtx 4090' in gpu or 'rtx 4080' in gpu:
        gpu_bonus = base_price * 0.20
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 40 High-End GPU)")
        gpu_applied = True
    elif 'rtx 4070' in gpu or 'rtx 4060' in gpu:
        gpu_bonus = base_price * 0.12
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 4060/4070 GPU)")
        gpu_applied = True
    elif 'rtx 4050' in gpu:
        gpu_bonus = base_price * 0.10
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 4050 GPU)")
        gpu_applied = True
    elif 'rtx 3060' in gpu:
        gpu_bonus = base_price * 0.08
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 3060 GPU)")
        gpu_applied = True
    elif 'rtx 3050' in gpu:
        gpu_bonus = base_price * 0.06
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 3050 GPU)")
        gpu_applied = True
    elif 'gtx 1650' in gpu:
        gpu_bonus = base_price * 0.04
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (GTX 1650 GPU)")
        gpu_applied = True
    elif 'amd radeon' in gpu or 'radeon' in gpu:
        gpu_bonus = base_price * 0.05
        final_price += gpu_bonus
        adjustments.append(f"+Rs.{int(gpu_bonus):,} (AMD Radeon GPU)")
        gpu_applied = True
    elif 'integrated' in gpu:
        # No adjustment for integrated graphics
        pass
    
    # If no GPU from dropdown, check text for GPU mentions
    if not gpu_applied:
        if any(x in text for x in ['rtx 4090', 'rtx 4080']):
            gpu_bonus = base_price * 0.20
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 40 High-End GPU)")
        elif any(x in text for x in ['rtx 4070', 'rtx 4060']):
            gpu_bonus = base_price * 0.12
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 4060/4070 GPU)")
        elif any(x in text for x in ['rtx 4050']):
            gpu_bonus = base_price * 0.10
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 4050 GPU)")
        elif any(x in text for x in ['rtx 3080', 'rtx 3070', 'rtx 3090']):
            gpu_bonus = base_price * 0.08
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 30 Series GPU)")
        elif any(x in text for x in ['rtx 3060', 'rtx 3050']):
            gpu_bonus = base_price * 0.06
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (RTX 30 Series GPU)")
        elif any(x in text for x in ['gtx 1660', 'gtx 1650', 'gtx 1050', 'mx350', 'mx450']):
            gpu_bonus = base_price * 0.04
            final_price += gpu_bonus
            adjustments.append(f"+Rs.{int(gpu_bonus):,} (Dedicated GPU)")
    
    return final_price, adjustments


# ============================================================================
# FURNITURE MARKET PRICES DATABASE
# ============================================================================
# Base prices in PKR for used furniture items in good condition
# Prices based on Pakistan furniture market (December 2024)

FURNITURE_MARKET_PRICES = {
    # BED prices by size
    'bed': {
        'single': {'base': 25000, 'new': 35000},
        'double': {'base': 40000, 'new': 55000},
        'queen': {'base': 55000, 'new': 75000},
        'king': {'base': 75000, 'new': 100000},
        'bunk': {'base': 45000, 'new': 65000},
        'default': {'base': 35000, 'new': 50000},
    },
    # TABLE prices by type
    'table': {
        'dining_4': {'base': 35000, 'new': 50000},
        'dining_6': {'base': 55000, 'new': 75000},
        'dining_8': {'base': 75000, 'new': 100000},
        'coffee': {'base': 15000, 'new': 22000},
        'side': {'base': 8000, 'new': 12000},
        'console': {'base': 20000, 'new': 30000},
        'study': {'base': 18000, 'new': 28000},
        'default': {'base': 25000, 'new': 35000},
    },
    # SOFA prices by type
    'sofa': {
        '2_seater': {'base': 35000, 'new': 50000},
        '3_seater': {'base': 50000, 'new': 70000},
        '5_seater': {'base': 75000, 'new': 100000},
        '7_seater': {'base': 100000, 'new': 140000},
        'l_shaped': {'base': 90000, 'new': 130000},
        'sectional': {'base': 120000, 'new': 170000},
        'sofa_cum_bed': {'base': 65000, 'new': 90000},
        'recliner': {'base': 80000, 'new': 120000},
        'default': {'base': 55000, 'new': 75000},
    },
    # CHAIR prices by type
    'chair': {
        'dining': {'base': 5000, 'new': 8000},
        'office': {'base': 15000, 'new': 25000},
        'gaming': {'base': 35000, 'new': 55000},
        'rocking': {'base': 18000, 'new': 28000},
        'accent': {'base': 12000, 'new': 20000},
        'bean_bag': {'base': 8000, 'new': 12000},
        'default': {'base': 10000, 'new': 15000},
    },
    # WARDROBE prices by size
    'wardrobe': {
        '2_door': {'base': 35000, 'new': 50000},
        '3_door': {'base': 50000, 'new': 70000},
        '4_door': {'base': 70000, 'new': 95000},
        'sliding': {'base': 80000, 'new': 110000},
        'walk_in': {'base': 150000, 'new': 220000},
        'default': {'base': 45000, 'new': 65000},
    },
    # DESK prices by type
    'desk': {
        'computer': {'base': 20000, 'new': 30000},
        'executive': {'base': 45000, 'new': 70000},
        'standing': {'base': 35000, 'new': 55000},
        'writing': {'base': 15000, 'new': 22000},
        'l_shaped': {'base': 40000, 'new': 60000},
        'default': {'base': 25000, 'new': 35000},
    },
    # CABINET prices by type
    'cabinet': {
        'kitchen': {'base': 30000, 'new': 45000},
        'bathroom': {'base': 15000, 'new': 22000},
        'storage': {'base': 20000, 'new': 30000},
        'display': {'base': 35000, 'new': 50000},
        'filing': {'base': 18000, 'new': 28000},
        'default': {'base': 22000, 'new': 32000},
    },
    # SHELF prices by type
    'shelf': {
        'bookshelf': {'base': 18000, 'new': 28000},
        'wall_shelf': {'base': 8000, 'new': 12000},
        'corner': {'base': 10000, 'new': 15000},
        'floating': {'base': 5000, 'new': 8000},
        'shoe_rack': {'base': 12000, 'new': 18000},
        'default': {'base': 12000, 'new': 18000},
    },
    # DRESSING TABLE prices
    'dressing_table': {
        'with_mirror': {'base': 25000, 'new': 38000},
        'with_storage': {'base': 30000, 'new': 45000},
        'vanity': {'base': 40000, 'new': 60000},
        'simple': {'base': 18000, 'new': 28000},
        'default': {'base': 25000, 'new': 38000},
    },
    # TV UNIT prices
    'tv_unit': {
        'wall_mount': {'base': 20000, 'new': 30000},
        'floor_standing': {'base': 25000, 'new': 38000},
        'entertainment_center': {'base': 45000, 'new': 65000},
        'simple': {'base': 15000, 'new': 22000},
        'default': {'base': 22000, 'new': 32000},
    },
    # Default for other furniture
    'other': {
        'default': {'base': 20000, 'new': 30000},
    }
}


def get_furniture_market_price(furniture_type: str, subtype: str, condition: str) -> Tuple[Optional[float], str]:
    """
    Get market price for furniture based on type and subtype
    Returns (price, category_tier)
    """
    furniture_type = furniture_type.lower().strip() if furniture_type else 'other'
    subtype = subtype.lower().strip() if subtype else 'default'
    condition = condition.lower().strip() if condition else 'used'
    
    # Get prices for this furniture type
    if furniture_type in FURNITURE_MARKET_PRICES:
        type_prices = FURNITURE_MARKET_PRICES[furniture_type]
    else:
        type_prices = FURNITURE_MARKET_PRICES['other']
    
    # Get subtype price or default
    if subtype in type_prices:
        prices = type_prices[subtype]
    else:
        prices = type_prices.get('default', {'base': 20000, 'new': 30000})
    
    # Return appropriate price based on condition
    if condition == 'new':
        return prices['new'], furniture_type
    else:
        return prices['base'], furniture_type


def apply_furniture_price_adjustments(base_price: float, data: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Apply realistic price adjustments for furniture based on attributes
    Returns adjusted price and list of adjustments made
    """
    adjustments = []
    final_price = base_price
    
    condition = data.get('condition', 'used').lower()
    
    # Condition adjustments (beyond the base new/used difference)
    if condition == 'refurbished':
        refurb_penalty = base_price * 0.10
        final_price -= refurb_penalty
        adjustments.append(f"-Rs.{int(refurb_penalty):,} (Refurbished)")
    elif condition == 'excellent':
        excellent_bonus = base_price * 0.08
        final_price += excellent_bonus
        adjustments.append(f"+Rs.{int(excellent_bonus):,} (Excellent condition)")
    elif condition == 'good':
        pass  # No adjustment for good used condition
    elif condition == 'fair':
        fair_penalty = base_price * 0.15
        final_price -= fair_penalty
        adjustments.append(f"-Rs.{int(fair_penalty):,} (Fair condition)")
    
    # Material premium adjustments
    material = data.get('material', '').lower()
    if material in ['sheesham', 'teak', 'walnut', 'oak', 'mahogany']:
        premium_bonus = base_price * 0.20
        final_price += premium_bonus
        adjustments.append(f"+Rs.{int(premium_bonus):,} (Premium {material.title()} Wood)")
    elif material in ['leather']:
        leather_bonus = base_price * 0.15
        final_price += leather_bonus
        adjustments.append(f"+Rs.{int(leather_bonus):,} (Leather)")
    elif material in ['marble', 'granite']:
        stone_bonus = base_price * 0.25
        final_price += stone_bonus
        adjustments.append(f"+Rs.{int(stone_bonus):,} ({material.title()})")
    elif material in ['glass']:
        glass_bonus = base_price * 0.05
        final_price += glass_bonus
        adjustments.append(f"+Rs.{int(glass_bonus):,} (Glass)")
    elif material in ['plastic', 'mdf']:
        budget_penalty = base_price * 0.15
        final_price -= budget_penalty
        adjustments.append(f"-Rs.{int(budget_penalty):,} (Budget Material)")
    
    # Antique bonus
    is_antique = data.get('is_antique', False)
    if is_antique:
        antique_bonus = base_price * 0.30
        final_price += antique_bonus
        adjustments.append(f"+Rs.{int(antique_bonus):,} (Antique)")
    
    # Handmade/Custom bonus
    is_handmade = data.get('is_handmade', False)
    if is_handmade:
        handmade_bonus = base_price * 0.15
        final_price += handmade_bonus
        adjustments.append(f"+Rs.{int(handmade_bonus):,} (Handmade)")
    
    # Imported bonus
    is_imported = data.get('is_imported', False)
    if is_imported:
        import_bonus = base_price * 0.20
        final_price += import_bonus
        adjustments.append(f"+Rs.{int(import_bonus):,} (Imported)")
    
    # Storage feature bonus
    has_storage = data.get('has_storage', False)
    if has_storage:
        storage_bonus = base_price * 0.08
        final_price += storage_bonus
        adjustments.append(f"+Rs.{int(storage_bonus):,} (With Storage)")
    
    # Seating capacity bonus (for sofas/chairs mainly)
    seating_capacity = data.get('seating_capacity', 0)
    furniture_type = data.get('furniture_type', '').lower()
    if seating_capacity > 0 and furniture_type not in ['sofa']:  # Sofa already has seating in subtype
        if seating_capacity >= 6:
            seating_bonus = base_price * 0.15
            final_price += seating_bonus
            adjustments.append(f"+Rs.{int(seating_bonus):,} ({seating_capacity}+ Seater)")
    
    return final_price, adjustments


def prepare_furniture_features(data: Dict[str, Any]) -> pd.DataFrame:
    """Prepare furniture features (use existing enhanced preprocessor)"""
    from ml_pipeline.enhanced_preprocessor import EnhancedPreprocessor
    
    # Create DataFrame from input
    df_input = pd.DataFrame([{
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'price': 0  # Placeholder
    }])
    
    preprocessor = EnhancedPreprocessor()
    X, _, _ = preprocessor.prepare_features(df_input, 'furniture')
    
    return X


@router.post("/predict-price", response_model=PricePredictionResponse)
def predict_price(request: PricePredictionRequest):
    """
    Predict optimal price using advanced ML models with strict title validation
    
    Models:
    - Laptop: XGBoost (92.29% R², MAE Rs.1,702)
    - Mobile: Gradient Boosting (99.94% R², MAE Rs.168)
    - Furniture: Gradient Boosting (99.96% R², MAE Rs.109)
    
    Request body:
    {
        "title": "Product title",
        "description": "Detailed description with specs",
        "category": "laptop" | "mobile" | "furniture",
        "condition": "new" | "used" | "refurbished"
    }
    
    The model will ONLY predict if the title contains relevant information:
    - Mobile: Must include brand/model name
    - Laptop: Must include brand and processor/model info
    - Furniture: Must include furniture type and material
    """
    
    try:
        category = request.category.lower()
        
        # Validate category
        if category not in ['laptop', 'mobile', 'furniture']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Must be 'laptop', 'mobile', or 'furniture'"
            )
        
        # Strict title validation before prediction
        title = request.dict().get('title', '')
        description = request.dict().get('description', '')
        material = request.dict().get('material', '')
        
        is_valid, error_msg, extracted_info = TitleValidator.validate_title(
            category, title, description, material=material
        )
        
        if not is_valid:
            hints = TitleValidator.get_validation_hints(category)
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Title validation failed",
                    "message": error_msg,
                    "hints": hints,
                    "extracted_info": extracted_info
                }
            )
        
        # Load model
        model_data = load_advanced_model(category)
        if not model_data:
            raise HTTPException(
                status_code=500,
                detail=f"Model not available for category: {category}"
            )
        
        model = model_data['model']
        scaler = model_data.get('scaler')
        
        # Prepare features based on category
        if category == 'laptop':
            # For laptop: Use market price database first, then fall back to ML model
            request_data = request.dict()
            condition = request_data.get('condition', 'used')
            
            # Try to get market price
            market_price, tier = get_laptop_market_price(title, condition)
            
            # Prepare features for ML model
            features = prepare_laptop_features_advanced(request_data)
            if scaler is not None:
                features_scaled = scaler.transform(features)
            else:
                features_scaled = features
            ml_predicted = model.predict(features_scaled)[0]
            
            if market_price:
                # Apply adjustments for warranty, SSD, RAM, etc.
                predicted_price, adjustments = apply_laptop_price_adjustments(market_price, request_data, tier or 'mid')
                
                # Build recommendation with adjustments
                adjustment_text = " | ".join(adjustments) if adjustments else "No adjustments"
                recommendation = f"Predicted price. Adjustments: {adjustment_text}"
            else:
                # Fall back to ML model for unknown models
                # Apply adjustments to ML prediction too
                predicted_price, adjustments = apply_laptop_price_adjustments(ml_predicted, request_data, 'mid')
                recommendation = f"Predicted price. Adjustments: {' | '.join(adjustments) if adjustments else 'None'}"
            
            predicted_price = max(25000, predicted_price)  # Minimum Rs.25,000 for laptops
            
            # Calculate price gap based on predicted amount (Rs. 5,000 - 7,000 total range)
            # Higher prices get larger gaps
            if predicted_price < 50000:
                price_gap = 5000
            elif predicted_price < 100000:
                price_gap = 5500
            elif predicted_price < 200000:
                price_gap = 6000
            elif predicted_price < 400000:
                price_gap = 6500
            else:
                price_gap = 7000
            
            half_gap = price_gap / 2
            confidence_lower = predicted_price - half_gap
            confidence_upper = predicted_price + half_gap
            
        elif category == 'mobile':
            # For mobile: Use market price database first, then fall back to ML model
            request_data = request.dict()
            condition = request_data.get('condition', 'used')
            
            # Try to get market price
            market_price = get_mobile_market_price(title, condition)
            
            # Prepare features for ML model
            features = prepare_mobile_features(request_data)
            if scaler is not None:
                features_scaled = scaler.transform(features)
            else:
                features_scaled = features
            ml_predicted = model.predict(features_scaled)[0]
            
            if market_price:
                # Apply adjustments for PTA, warranty, box, etc.
                predicted_price, adjustments = apply_mobile_price_adjustments(market_price, request_data)
                
                # Build recommendation with adjustments
                adjustment_text = " | ".join(adjustments) if adjustments else "No adjustments"
                recommendation = f"Predicted price. Adjustments: {adjustment_text}"
            else:
                # Fall back to ML model for unknown models
                # Apply adjustments to ML prediction too
                predicted_price, adjustments = apply_mobile_price_adjustments(ml_predicted, request_data)
                recommendation = f"Predicted price. Adjustments: {' | '.join(adjustments) if adjustments else 'None'}"
            
            predicted_price = max(5000, predicted_price)  # Minimum Rs.5,000 for mobiles
            
            # Calculate price gap based on predicted amount (Rs. 5,000 - 7,000 total range)
            # Higher prices get larger gaps
            if predicted_price < 20000:
                price_gap = 5000
            elif predicted_price < 50000:
                price_gap = 5500
            elif predicted_price < 100000:
                price_gap = 6000
            elif predicted_price < 200000:
                price_gap = 6500
            else:
                price_gap = 7000
            
            half_gap = price_gap / 2
            confidence_lower = predicted_price - half_gap
            confidence_upper = predicted_price + half_gap
            
        elif category == 'furniture':
            # For furniture: Use market price database first, then fall back to ML model
            request_data = request.dict()
            condition = request_data.get('condition', 'used')
            furniture_type = request_data.get('furniture_type', '')
            furniture_subtype = request_data.get('furniture_subtype', '')
            
            # Try to get market price based on type and subtype
            market_price, tier = get_furniture_market_price(furniture_type, furniture_subtype, condition)
            
            # Prepare features for ML model (as fallback/reference)
            features = prepare_furniture_features(request_data)
            if scaler is not None:
                features_scaled = scaler.transform(features)
            else:
                features_scaled = features
            ml_predicted = model.predict(features_scaled)[0]
            
            if market_price and furniture_type:
                # Apply adjustments for material, antique, handmade, etc.
                predicted_price, adjustments = apply_furniture_price_adjustments(market_price, request_data)
                
                # Build recommendation with adjustments
                adjustment_text = " | ".join(adjustments) if adjustments else "No adjustments"
                recommendation = f"Predicted price. Adjustments: {adjustment_text}"
            else:
                # Fall back to ML model for unknown types
                predicted_price, adjustments = apply_furniture_price_adjustments(ml_predicted, request_data)
                recommendation = f"Predicted price. Adjustments: {' | '.join(adjustments) if adjustments else 'None'}"
            
            predicted_price = max(2000, predicted_price)  # Minimum Rs.2,000 for furniture
            
            # Calculate price gap based on predicted amount (Rs. 5,000 - 7,000 total range)
            # Higher prices get larger gaps
            if predicted_price < 10000:
                price_gap = 5000
            elif predicted_price < 30000:
                price_gap = 5500
            elif predicted_price < 60000:
                price_gap = 6000
            elif predicted_price < 100000:
                price_gap = 6500
            else:
                price_gap = 7000
            
            half_gap = price_gap / 2
            confidence_lower = max(2000, predicted_price - half_gap)
            confidence_upper = predicted_price + half_gap
        
        # Get model metadata for response
        metadata = model_data.get('metadata', {})
        model_accuracy = metadata.get('test_r2', 0.92) if category == 'laptop' else metadata.get('r2_score', 0.99)
        
        return PricePredictionResponse(
            predicted_price=round(predicted_price, 2),
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2),
            confidence_score=round(model_accuracy, 2),
            recommendation=recommendation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


def _get_pricing_recommendation(price: float, category: str) -> str:
    """Generate pricing recommendation based on predicted price"""
    
    if category == 'laptop':
        if price < 25000:
            return "Budget laptop - Price competitively for quick sale"
        elif price < 50000:
            return "Mid-range laptop - Good market demand at this price point"
        elif price < 80000:
            return "Premium laptop - Highlight performance specs to justify price"
        else:
            return "High-end laptop - Target serious buyers, emphasize condition"
    
    elif category == 'mobile':
        if price < 15000:
            return "Entry-level phone - Price slightly below prediction for faster sale"
        elif price < 40000:
            return "Mid-range phone - Competitive market, highlight unique features"
        elif price < 80000:
            return "Flagship phone - Emphasize warranty and accessories"
        else:
            return "Ultra-premium - Target collectors, emphasize exclusivity"
    
    elif category == 'furniture':
        if price < 10000:
            return "Budget furniture - Quick sale likely at this price"
        elif price < 30000:
            return "Mid-range furniture - Good quality-to-price ratio"
        else:
            return "Premium furniture - Emphasize material quality and craftsmanship"
    
    return "Price seems reasonable for this category"


@router.get("/model-info/{category}")
def get_model_info(category: str):
    """Get information about the prediction model for a category"""
    
    model_data = load_advanced_model(category)
    if not model_data:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for category: {category}"
        )
    
    metadata = model_data.get('metadata', {})
    
    return {
        "category": category,
        "model_type": type(model_data['model']).__name__,
        "accuracy_r2": metadata.get('test_r2', metadata.get('r2_score', 'N/A')),
        "mae": metadata.get('mae', 'N/A'),
        "mape": metadata.get('mape', 'N/A'),
        "training_samples": metadata.get('training_samples', 'N/A'),
        "features_count": metadata.get('features_count', 'N/A'),
        "last_trained": metadata.get('trained_date', 'N/A'),
        "status": "Production Ready ✓"
    }


@router.post("/predict-price-with-dropdowns", response_model=PricePredictionResponse)
def predict_price_with_dropdowns(request: PricePredictionRequest):
    """
    Predict price using dropdown selections (frontend compatibility endpoint)
    This endpoint maintains backward compatibility with the existing frontend
    
    Same functionality as /predict-price but with different naming
    """
    return predict_price(request)


@router.get("/validate-title")
@router.post("/validate-title")
def validate_title(category: str, title: str, description: str = "", material: str = ""):
    """
    Validate that title contains relevant information for the category
    Returns validation status and helpful error messages
    
    Args:
        category: 'mobile', 'laptop', or 'furniture'
        title: Product title to validate
        description: Product description (optional, helps with validation)
        material: Material (required for furniture)
    
    Returns:
        {
            "is_valid": bool,
            "message": str,
            "extracted_info": dict,
            "hints": dict
        }
    """
    try:
        is_valid, error_msg, extracted_info = TitleValidator.validate_title(
            category, title, description, material=material
        )
        
        hints = TitleValidator.get_validation_hints(category)
        
        if is_valid:
            return {
                "is_valid": True,
                "message": "Title is valid and contains relevant information",
                "extracted_info": extracted_info,
                "hints": hints
            }
        else:
            return {
                "is_valid": False,
                "message": error_msg,
                "extracted_info": extracted_info,
                "hints": hints
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/dropdown-options/{category}")
def get_dropdown_options(category: str) -> Dict[str, List]:
    """
    Get dropdown options for a specific category
    Returns encoded label values for UI dropdowns
    
    Args:
        category: 'mobile', 'laptop', or 'furniture'
    
    Returns:
        Dictionary with dropdown options for each field
    """
    
    if category == 'mobile':
        return {
            "condition": ["new", "used", "refurbished"],
            "brands": [
                "Apple", "Samsung", "Xiaomi", "Oppo", "Vivo", "Realme", 
                "OnePlus", "Huawei", "Google", "Nokia", "Motorola",
                "Tecno", "Infinix", "Itel", "QMobile"
            ],
            "ram_options": [2, 3, 4, 6, 8, 12, 16, 18, 24],
            "storage_options": [16, 32, 64, 128, 256, 512, 1024],
            "battery_options": [0, 3000, 4000, 5000, 6000, 7000],  # 0 = Unknown
            "camera_options": [0, 12, 13, 16, 20, 32, 48, 50, 64, 108, 200],  # 0 = Unknown
            "screen_size_options": [0, 5.5, 6.0, 6.1, 6.5, 6.7, 6.8, 7.0],  # 0 = Unknown
            "boolean_features": {
                "has_5g": "5G Support",
                "has_pta": "PTA Approved",
                "has_amoled": "AMOLED Display",
                "has_warranty": "Warranty Included",
                "has_box": "Original Box"
            }
        }
    
    elif category == 'laptop':
        return {
            "condition": ["new", "used", "refurbished"],
            "brands": [
                "Dell", "HP", "Lenovo", "Asus", "Acer", "Apple", "MSI",
                "Razer", "Alienware", "Microsoft Surface", "Samsung", "LG"
            ],
            "processors": [
                "Intel Core i3", "Intel Core i5", "Intel Core i7", "Intel Core i9",
                "AMD Ryzen 3", "AMD Ryzen 5", "AMD Ryzen 7", "AMD Ryzen 9",
                "Apple M1", "Apple M2", "Apple M3", "Intel Pentium", "Intel Celeron"
            ],
            "generation_options": [6, 7, 8, 9, 10, 11, 12, 13, 14],  # Intel/AMD generation
            "ram_options": [4, 8, 12, 16, 24, 32, 64],
            "storage_options": [128, 256, 512, 1024, 2048],
            "gpu_options": [
                "None (Integrated)", "NVIDIA GTX 1650", "NVIDIA RTX 3050",
                "NVIDIA RTX 3060", "NVIDIA RTX 4050", "NVIDIA RTX 4060",
                "AMD Radeon RX 6600M", "AMD Radeon RX 6700M"
            ],
            "screen_size_options": [13.3, 14.0, 15.6, 16.0, 17.3],
            "boolean_features": {
                "has_ssd": "SSD Storage",
                "is_gaming": "Gaming Laptop",
                "is_touchscreen": "Touchscreen",
                "has_backlit_keyboard": "Backlit Keyboard",
                "has_fingerprint": "Fingerprint Reader"
            }
        }
    
    elif category == 'furniture':
        return {
            "condition": ["new", "used", "refurbished"],
            "materials": [
                "Wood", "Solid Wood", "Oak", "Pine", "Walnut", "Teak", "Mahogany",
                "Metal", "Steel", "Iron", "Aluminum",
                "Leather", "Genuine Leather", "Faux Leather",
                "Fabric", "Velvet", "Linen", "Cotton",
                "Plastic", "Glass", "Marble", "Rattan", "Wicker", "Bamboo",
                "MDF", "Plywood", "Laminate"
            ],
            "furniture_types": [
                "Sofa", "Couch", "Chair", "Dining Table", "Coffee Table",
                "Bed", "Wardrobe", "Cabinet", "Shelf", "Desk", "Dresser",
                "Ottoman", "Recliner", "Sectional", "Bench", "Stool"
            ],
            "seating_capacity_options": [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12],  # 0 = Not applicable
            "boolean_features": {
                "is_imported": "Imported",
                "is_handmade": "Handmade",
                "has_storage": "With Storage",
                "is_modern": "Modern Design",
                "is_antique": "Antique/Vintage",
                "is_foldable": "Foldable"
            }
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Must be 'mobile', 'laptop', or 'furniture'"
        )


@router.get("/validation-hints/{category}")
def get_validation_hints(category: str) -> Dict:
    """
    Get helpful hints for creating valid titles for a category
    
    Args:
        category: 'mobile', 'laptop', or 'furniture'
    
    Returns:
        Dictionary with required fields, recommended fields, and example
    """
    hints = TitleValidator.get_validation_hints(category)
    if not hints:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}"
        )
    return hints
