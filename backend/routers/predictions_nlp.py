"""
🔮 AI-Powered Price Prediction API - NLP-Based
Production-ready prediction endpoint using NLP feature extraction
"""

from fastapi import APIRouter, HTTPException
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any

from schemas.schemas import PricePredictionRequest, PricePredictionResponse
from nlp_feature_extractor import get_feature_extractor
from brand_categorization import (
    get_brand_score, get_material_score, get_condition_score,
    get_processor_tier, get_gpu_tier, get_dropdown_options
)

router = APIRouter()

# Paths
models_path = Path(__file__).parent.parent / "trained_models"

# Cache loaded models
_loaded_models = {}


def load_model(category: str):
    """Load pre-trained model for category"""
    if category in _loaded_models:
        return _loaded_models[category]
    
    try:
        model_file = models_path / f"{category}_model.pkl"
        scaler_file = models_path / f"{category}_scaler.pkl"
        metadata_file = models_path / f"model_metadata_{category}.json"
        
        if not model_file.exists():
            return None
        
        # Load ensemble model (dict with xgb, lgb, rf, gb, weights)
        ensemble = joblib.load(model_file)
        
        # Load scaler (separate file)
        scaler = None
        if scaler_file.exists():
            scaler = joblib.load(scaler_file)
        
        # Load metadata
        metadata = None
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        _loaded_models[category] = {
            'ensemble': ensemble,
            'scaler': scaler,
            'metadata': metadata
        }
        
        return _loaded_models[category]
    
    except Exception as e:
        print(f"Error loading model for {category}: {e}")
        return None


def make_ensemble_prediction(ensemble_data: Dict, features_df: pd.DataFrame) -> float:
    """Make prediction using ensemble model"""
    ensemble = ensemble_data['ensemble']
    scaler = ensemble_data['scaler']
    
    # Get models and weights from ensemble dict
    # Structure: {'xgb': model, 'lgb': model, 'rf': model, 'gb': model, 'weights': [0.35, 0.35, 0.15, 0.15]}
    models_list = [ensemble['xgb'], ensemble['lgb'], ensemble['rf'], ensemble['gb']]
    weights_list = ensemble['weights']
    
    # Scale features if scaler exists
    if scaler is not None:
        features_scaled = scaler.transform(features_df)
    else:
        features_scaled = features_df.values
    
    # Ensemble prediction with weighted average
    prediction = 0
    for model, weight in zip(models_list, weights_list):
        pred = model.predict(features_scaled)[0]
        prediction += pred * weight
    
    return max(0, prediction)  # Ensure non-negative


@router.post("/predict-price", response_model=PricePredictionResponse)
def predict_price(request: PricePredictionRequest):
    """
    Predict optimal price for an item using NLP-based feature extraction
    
    Request body:
    {
        "category": "mobile|laptop|furniture",
        "features": {
            "title": "Product title",
            "description": "Product description (optional)",
            "brand": "Brand name (optional)",
            "condition": "new|excellent|good|fair|poor (optional)"
        }
    }
    """
    
    category = request.category.lower()
    features = request.features
    
    # Validate category
    if category not in ["mobile", "laptop", "furniture"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid category. Must be 'mobile', 'laptop', or 'furniture'"
        )
    
    # Load model
    model_data = load_model(category)
    if not model_data:
        raise HTTPException(
            status_code=500,
            detail=f"Model for category '{category}' not found. Please train the model first."
        )
    
    try:
        # Get NLP feature extractor
        extractor = get_feature_extractor()
        
        # Extract features from text
        title = features.get('title', '')
        description = features.get('description', '')
        
        if category == 'mobile':
            extracted = extractor.extract_mobile_features(title, description)
        elif category == 'laptop':
            extracted = extractor.extract_laptop_features(title, description)
        elif category == 'furniture':
            extracted = extractor.extract_furniture_features(title, description)
        
        # Add engineered features
        extracted = extractor.create_engineered_features(extracted, category)
        
        # Override with user-provided values if available
        if 'condition' in features:
            extracted['condition_score'] = extractor.extract_condition_score(features['condition'])
        
        # Convert to DataFrame
        features_df = pd.DataFrame([extracted])
        
        # Make prediction
        predicted_price = make_ensemble_prediction(model_data, features_df)
        
        # Calculate confidence based on R² score
        metadata = model_data.get('metadata', {})
        r2_score = metadata.get('metrics', {}).get('r2_score', 0.75)
        confidence_score = r2_score
        
        # Calculate price range (±20%)
        margin = 0.20
        price_range_min = predicted_price * (1 - margin)
        price_range_max = predicted_price * (1 + margin)
        
        # Prepare response
        response = {
            "predicted_price": round(predicted_price, 2),
            "confidence_score": round(confidence_score, 4),
            "price_range_min": round(price_range_min, 2),
            "price_range_max": round(price_range_max, 2),
            "currency": "PKR",
            "category": category,
            "extracted_features": {k: (float(v) if isinstance(v, (np.integer, np.floating)) else v) 
                                   for k, v in extracted.items()}
        }
        
        return PricePredictionResponse(**response)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during prediction: {str(e)}"
        )


@router.post("/predict-price-with-dropdowns", response_model=PricePredictionResponse)
def predict_price_with_dropdowns(request: Dict[str, Any]):
    """
    Predict price using dropdown-selected features (for frontend)
    
    Request body structure varies by category:
    
    MOBILE:
    {
        "category": "mobile",
        "brand": "Samsung|Apple|Xiaomi|...",
        "ram": 4|6|8|12|16,
        "storage": 64|128|256|512,
        "condition": "new|excellent|good|fair|poor",
        "camera": 12|48|108|... (optional),
        "battery": 4000|5000|... (optional),
        "screen_size": 6.1|6.7|... (optional),
        "has_5g": true|false,
        "has_pta": true|false,
        "has_amoled": true|false,
        "has_warranty": true|false,
        "has_box": true|false,
        "age_months": 0|6|12|24|...
    }
    
    LAPTOP:
    {
        "category": "laptop",
        "brand": "Dell|HP|Apple|...",
        "processor": "i3|i5|i7|i9|Ryzen 5|...",
        "generation": 8|9|10|11|12|13,
        "ram": 4|8|16|32,
        "storage": 256|512|1024,
        "gpu": "None|GTX 1650|RTX 3050|...",
        "condition": "new|excellent|good|fair|poor",
        "screen_size": 13.3|15.6|17.3,
        "has_ssd": true|false,
        "is_gaming": true|false,
        "is_touchscreen": true|false,
        "age_months": 0|6|12|24|...
    }
    
    FURNITURE:
    {
        "category": "furniture",
        "material": "Teak|Wood|Metal|...",
        "seating_capacity": 0|2|3|5|7,
        "length": 150|200|... (cm),
        "width": 80|100|... (cm),
        "height": 85|95|... (cm),
        "condition": "new|excellent|good|fair|poor",
        "is_imported": true|false,
        "is_handmade": true|false,
        "has_storage": true|false,
        "is_modern": true|false,
        "is_antique": true|false
    }
    """
    
    category = request.get('category', '').lower()
    
    if category not in ["mobile", "laptop", "furniture"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid category"
        )
    
    # Load model
    model_data = load_model(category)
    if not model_data:
        raise HTTPException(
            status_code=500,
            detail=f"Model not found for {category}"
        )
    
    try:
        extractor = get_feature_extractor()
        
        # Build features dict based on category
        if category == 'mobile':
            features = {
                'brand_premium': get_brand_score(request.get('brand', ''), 'mobile'),
                'ram': request.get('ram', 4),
                'storage': request.get('storage', 64),
                'battery': request.get('battery', 0),
                'camera': request.get('camera', 0),
                'screen_size': request.get('screen_size', 0),
                'is_5g': 1 if request.get('has_5g', False) else 0,
                'is_pta': 1 if request.get('has_pta', False) else 0,
                'is_amoled': 1 if request.get('has_amoled', False) else 0,
                'has_warranty': 1 if request.get('has_warranty', False) else 0,
                'has_box': 1 if request.get('has_box', False) else 0,
                'condition_score': get_condition_score(request.get('condition', 'good')),
                'age_months': request.get('age_months', 12),
            }
            
            # Add engineered features
            features = extractor.create_engineered_features(features, category)
            
            # TEMP: Add price_category as mid-range estimate (needed by current models)
            # This will be removed once models are retrained without it
            features['price_category'] = 3
        
        elif category == 'laptop':
            features = {
                'brand_premium': get_brand_score(request.get('brand', ''), 'laptop'),
                'processor_tier': get_processor_tier(request.get('processor', '')),
                'generation': request.get('generation', 10),
                'ram': request.get('ram', 8),
                'storage': request.get('storage', 256),
                'has_gpu': 1 if request.get('gpu', 'None') != 'None' else 0,
                'gpu_tier': get_gpu_tier(request.get('gpu', '')),
                'is_gaming': 1 if request.get('is_gaming', False) else 0,
                'is_touchscreen': 1 if request.get('is_touchscreen', False) else 0,
                'has_ssd': 1 if request.get('has_ssd', True) else 0,
                'screen_size': request.get('screen_size', 15.6),
                'condition_score': get_condition_score(request.get('condition', 'good')),
                'age_months': request.get('age_months', 12),
            }
            
            # Add engineered features
            features = extractor.create_engineered_features(features, category)
            
            # TEMP: Add price_category as mid-range estimate
            features['price_category'] = 3
        
        elif category == 'furniture':
            features = {
                'material_quality': get_material_score(request.get('material', '')),
                'seating_capacity': request.get('seating_capacity', 0),
                'length': request.get('length', 0),
                'width': request.get('width', 0),
                'height': request.get('height', 0),
                'volume': request.get('length', 0) * request.get('width', 0) * request.get('height', 0),
                'is_imported': 1 if request.get('is_imported', False) else 0,
                'is_handmade': 1 if request.get('is_handmade', False) else 0,
                'has_storage': 1 if request.get('has_storage', False) else 0,
                'is_modern': 1 if request.get('is_modern', False) else 0,
                'is_antique': 1 if request.get('is_antique', False) else 0,
                'condition_score': get_condition_score(request.get('condition', 'good')),
            }
            
            # Add engineered features  
            features = extractor.create_engineered_features(features, category)
            
            # TEMP: Add price_category as mid-range estimate
            features['price_category'] = 3
        
        # Convert to DataFrame
        features_df = pd.DataFrame([features])
        
        # Make prediction
        predicted_price = make_ensemble_prediction(model_data, features_df)
        
        # Calculate confidence and range
        metadata = model_data.get('metadata', {})
        r2_score = metadata.get('metrics', {}).get('r2_score', 0.75)
        
        margin = 0.20
        response = {
            "predicted_price": round(predicted_price, 2),
            "confidence_score": round(r2_score, 4),
            "price_range_min": round(predicted_price * (1 - margin), 2),
            "price_range_max": round(predicted_price * (1 + margin), 2),
            "currency": "PKR",
            "category": category,
            "extracted_features": {k: (float(v) if isinstance(v, (np.integer, np.floating)) else v) 
                                   for k, v in features.items()}
        }
        
        return PricePredictionResponse(**response)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@router.get("/prediction-options/{category}")
def get_prediction_options(category: str):
    """
    Get dropdown options for a category (for frontend forms)
    Uses brand categorization system for organized selections
    """
    category = category.lower()
    
    if category not in ["mobile", "laptop", "furniture"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    # Get organized options from brand categorization
    options = get_dropdown_options(category)
    
    # Add boolean features
    if category == 'mobile':
        options["boolean_features"] = ["has_5g", "has_pta", "has_amoled", "has_warranty", "has_box"]
    elif category == 'laptop':
        options["boolean_features"] = ["has_ssd", "is_gaming", "is_touchscreen"]
    elif category == 'furniture':
        options["boolean_features"] = ["is_imported", "is_handmade", "has_storage", "is_modern", "is_antique"]
    
    return options
