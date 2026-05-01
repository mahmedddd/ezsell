"""
Enhanced Price Prediction Router
Validates inputs, extracts features using NLP, and prevents predictions without required data
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Union
import joblib
import logging
from pathlib import Path
import numpy as np

from schemas.prediction_schemas import (
    MobilePredictionInput,
    LaptopPredictionInput,
    FurniturePredictionInput,
    PredictionResponse,
    ErrorResponse,
    CategoryEnum
)
from ml_pipeline.advanced_feature_extractor import AdvancedFeatureExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["predictions"])

# Initialize feature extractor
feature_extractor = AdvancedFeatureExtractor()

# Model paths
MODELS_DIR = Path("models_enhanced")
FALLBACK_MODELS_DIR = Path(".")

def load_model(category: str):
    """Load enhanced model with fallback"""
    enhanced_path = MODELS_DIR / f"price_predictor_{category}_enhanced.pkl"
    fallback_path = FALLBACK_MODELS_DIR / f"price_predictor_{category}.pkl"
    
    try:
        if enhanced_path.exists():
            model = joblib.load(str(enhanced_path))
            logger.info(f"Loaded enhanced {category} model")
            return model, "enhanced"
        elif fallback_path.exists():
            model = joblib.load(str(fallback_path))
            logger.info(f"Loaded fallback {category} model")
            return model, "fallback"
        else:
            raise FileNotFoundError(f"No model found for {category}")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")

def validate_critical_fields(data: Dict[str, Any], category: str) -> tuple[bool, str]:
    """
    Validate that critical fields are present for accurate prediction
    Returns (is_valid, error_message)
    """
    # Check title
    if not data.get('title') or len(data['title'].strip()) < 10:
        return False, "Title is required and must be at least 10 characters for accurate prediction"
    
    # Check description
    if not data.get('description') or len(data['description'].strip()) < 20:
        return False, "Description is required and must be at least 20 characters for accurate prediction"
    
    # Check condition
    if not data.get('condition'):
        return False, "Condition (new/used/refurbished) is required for accurate prediction"
    
    # Category-specific validation
    if category == 'furniture':
        if not data.get('material') or len(data['material'].strip()) < 3:
            return False, "Material is required for furniture price prediction (e.g., wood, metal, leather)"
    
    return True, ""

def extract_and_prepare_features(data: Dict[str, Any], category: str) -> Dict[str, Any]:
    """
    Extract features from user input using NLP and regex
    Returns feature dictionary ready for prediction
    """
    # Combine title and description for extraction
    combined_text = f"{data.get('title', '')} {data.get('description', '')}"
    
    # Extract features based on category
    if category == 'mobile':
        features = feature_extractor.extract_mobile_features(combined_text)
        
        # Override with user-provided values if available
        if data.get('brand'):
            features['brand'] = data['brand']
        if data.get('ram'):
            features['ram'] = data['ram']
        if data.get('storage'):
            features['storage'] = data['storage']
        if data.get('battery'):
            features['battery'] = data['battery']
        if data.get('camera'):
            features['camera'] = data['camera']
        if data.get('screen_size'):
            features['screen_size'] = data['screen_size']
        
        # Add condition
        features['condition'] = data.get('condition', 'used')
        features['is_new'] = 1 if features['condition'] == 'new' else 0
        features['is_used'] = 1 if features['condition'] == 'used' else 0
        
    elif category == 'laptop':
        features = feature_extractor.extract_laptop_features(combined_text)
        
        # Override with user-provided values
        if data.get('brand'):
            features['brand'] = data['brand']
        if data.get('ram'):
            features['ram'] = data['ram']
        if data.get('storage'):
            features['storage'] = data['storage']
        if data.get('screen_size'):
            features['screen_size'] = data['screen_size']
        if data.get('processor'):
            # Re-extract processor features with user input
            proc_features = feature_extractor._extract_laptop_processor_detailed(data['processor'])
            features.update(proc_features)
        
        features['condition'] = data.get('condition', 'used')
        features['is_new'] = 1 if features['condition'] == 'new' else 0
        features['is_used'] = 1 if features['condition'] == 'used' else 0
        
    elif category == 'furniture':
        features = feature_extractor.extract_furniture_features(combined_text)
        
        # Material is required - ensure it's included
        material_text = data.get('material', '')
        material_features = feature_extractor._extract_furniture_material_detailed(material_text)
        features.update(material_features)
        
        # Override with user-provided values
        if data.get('furniture_type'):
            features['furniture_type'] = feature_extractor._extract_furniture_type(data['furniture_type'])
        if data.get('dimensions'):
            dim_features = feature_extractor._extract_dimensions(data['dimensions'])
            features.update(dim_features)
        if data.get('seating_capacity'):
            features['seating_capacity'] = data['seating_capacity']
        
        features['condition'] = data.get('condition', 'used')
        features['is_new'] = 1 if features['condition'] == 'new' else 0
        features['is_used'] = 1 if features['condition'] == 'used' else 0
    
    return features

def compute_advanced_features(features: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Compute advanced features like ratios, scores, etc."""
    
    if category == 'mobile':
        # Fill defaults
        features['ram'] = features.get('ram', 4)
        features['storage'] = features.get('storage', 64)
        features['battery'] = features.get('battery', 4000)
        features['camera'] = features.get('camera', 12)
        features['screen_size'] = features.get('screen_size', 6.0)
        
        # Compute advanced features
        features['ram_storage_ratio'] = features['ram'] / (features['storage'] + 1)
        features['capacity_score'] = (
            features['ram'] * 0.3 +
            features['storage'] / 10 * 0.3 +
            features['battery'] / 100 * 0.2 +
            features['camera'] * 0.1 +
            features['screen_size'] * 2 * 0.1
        )
        features['tech_score'] = (
            features.get('is_5g', 0) * 3 +
            features.get('is_amoled', 0) * 2 +
            features.get('processor_type', 0) +
            features.get('is_pta', 0)
        )
        features['completeness_score'] = (
            features.get('with_box', 0) +
            features.get('with_charger', 0) +
            features.get('with_accessories', 0) +
            features.get('has_warranty', 0) * 2
        )
        features['age_factor'] = np.exp(-0.1 * (2025 - features.get('model_year', 2023)))
        features['price_per_gb'] = 0  # Will be computed after prediction
        features['premium_ram_interaction'] = features.get('brand_premium', 3) * features['ram']
        features['premium_storage_interaction'] = features.get('brand_premium', 3) * features['storage']
        
        # Dummy price-based features (set to median values)
        features['storage_per_price'] = 0.001
        features['ram_per_price'] = 0.0001
        
    elif category == 'laptop':
        features['ram'] = features.get('ram', 8)
        features['storage'] = features.get('storage', 256)
        features['screen_size'] = features.get('screen_size', 15.6)
        
        features['processor_score'] = (
            features.get('processor_tier', 2) * 2 +
            features.get('processor_generation', 10) * 0.5 +
            features.get('processor_brand', 1)
        )
        features['storage_score'] = (
            features['storage'] / 100 +
            features.get('storage_type_score', 1) * 5
        )
        features['graphics_score'] = (
            features.get('gpu_tier', 0) * 3 +
            features.get('has_dedicated_gpu', 0) * 5
        )
        features['gaming_score'] = (
            features.get('processor_tier', 2) * 2 +
            features.get('gpu_tier', 0) * 3 +
            (features['ram'] / 4) +
            features.get('is_gaming', 0) * 5
        )
        features['portability_score'] = (15 - features['screen_size']) * features.get('battery_wh', 50) / 50
        features['features_score'] = (
            features.get('is_touchscreen', 0) * 2 +
            features.get('is_2in1', 0) * 3 +
            features.get('has_backlit', 0) +
            features.get('is_fullhd', 0) * 2 +
            features.get('is_4k', 0) * 4
        )
        features['capacity_score'] = (
            features['ram'] * 0.4 +
            features['storage'] / 50 * 0.3 +
            features['processor_score'] * 0.3
        )
        features['age_factor'] = np.exp(-0.15 * (2025 - features.get('model_year', 2023)))
        features['premium_spec_score'] = (
            features.get('brand_premium', 3) *
            (features['ram'] + features['storage'] / 100 + features['processor_score'])
        )
        
    elif category == 'furniture':
        features['seating_capacity'] = features.get('seating_capacity', 0)
        features['length'] = features.get('length', 150)
        features['width'] = features.get('width', 80)
        features['height'] = features.get('height', 80)
        features['volume'] = features['length'] * features['width'] * features['height']
        
        features['size_score'] = np.log1p(features['volume'])
        features['material_score'] = (
            features.get('material_quality', 2) * 2 +
            features.get('material_type', 0)
        )
        features['style_score'] = (
            features.get('is_modern', 0) * 2 +
            features.get('is_antique', 0) * 3 +
            features.get('is_imported', 0) * 2
        )
        features['completeness_score'] = (
            features.get('with_cushions', 0) +
            features.get('has_warranty', 0) * 2 +
            features.get('has_brand', 0) * 2
        )
        features['quality_score'] = (
            features.get('condition_score', 5) +
            features['material_score'] +
            features.get('is_handmade', 0) * 3
        )
        features['capacity_score'] = features['seating_capacity'] * features['size_score']
        features['price_per_volume'] = 0  # Will be computed after prediction
        features['type_material_score'] = features.get('furniture_type', 0) * features['material_score']
    
    return features

def prepare_feature_array(features: Dict[str, Any], category: str) -> np.ndarray:
    """Prepare feature array in correct order for model"""
    
    if category == 'mobile':
        feature_order = [
            'ram', 'storage', 'battery', 'camera', 'screen_size',
            'ram_storage_ratio', 'storage_per_price', 'ram_per_price',
            'capacity_score', 'tech_score', 'completeness_score',
            'age_factor', 'price_per_gb', 'premium_ram_interaction',
            'premium_storage_interaction', 'condition_score',
            'is_pta', 'non_pta', 'is_5g', 'is_amoled',
            'brand_premium', 'processor_type', 'with_box', 'has_warranty'
        ]
    elif category == 'laptop':
        feature_order = [
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
        feature_order = [
            'volume', 'length', 'width', 'height', 'seating_capacity',
            'size_score', 'material_score', 'style_score',
            'completeness_score', 'quality_score', 'capacity_score',
            'price_per_volume', 'type_material_score', 'condition_score',
            'furniture_type', 'material_quality', 'material_type',
            'is_sofa', 'is_bed', 'is_table', 'is_chair',
            'is_imported', 'is_antique', 'has_brand'
        ]
    
    # Build feature array
    feature_array = []
    for feat in feature_order:
        value = features.get(feat, 0)
        # Ensure numeric
        if value is None:
            value = 0
        feature_array.append(float(value))
    
    return np.array([feature_array])

@router.post("/mobile", response_model=Union[PredictionResponse, ErrorResponse])
async def predict_mobile_price(input_data: MobilePredictionInput):
    """Predict mobile phone price with validation"""
    
    try:
        # Convert to dict
        data = input_data.dict()
        
        # Validate critical fields
        is_valid, error_msg = validate_critical_fields(data, 'mobile')
        if not is_valid:
            return ErrorResponse(
                error=error_msg,
                details={"category": "mobile", "missing_field": error_msg.split(':')[0]}
            )
        
        # Extract features using NLP
        features = extract_and_prepare_features(data, 'mobile')
        
        # Compute advanced features
        features = compute_advanced_features(features, 'mobile')
        
        # Load model
        model, model_type = load_model('mobile')
        
        # Prepare feature array
        X = prepare_feature_array(features, 'mobile')
        
        # Predict
        predicted_price = float(model.predict(X)[0])
        
        # Calculate confidence based on feature completeness
        completeness = sum([
            1 if features.get('ram') else 0,
            1 if features.get('storage') else 0,
            1 if features.get('battery') else 0,
            1 if features.get('brand_premium', 0) > 0 else 0
        ]) / 4
        
        confidence = "high" if completeness > 0.75 else "medium" if completeness > 0.5 else "low"
        
        # Price range (±5% for high confidence, ±10% otherwise)
        margin = 0.05 if confidence == "high" else 0.10
        
        return PredictionResponse(
            success=True,
            category="mobile",
            predicted_price=round(predicted_price, 2),
            confidence=confidence,
            price_range={
                "min": round(predicted_price * (1 - margin), 2),
                "max": round(predicted_price * (1 + margin), 2)
            },
            extracted_features={k: v for k, v in features.items() if k in ['brand_premium', 'ram', 'storage', 'battery', 'camera', 'is_5g', 'is_pta', 'is_amoled']},
            message=f"Price predicted successfully using {model_type} model with {confidence} confidence"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return ErrorResponse(
            error="Prediction failed",
            details={"message": str(e)}
        )

@router.post("/laptop", response_model=Union[PredictionResponse, ErrorResponse])
async def predict_laptop_price(input_data: LaptopPredictionInput):
    """Predict laptop price with validation"""
    
    try:
        data = input_data.dict()
        
        is_valid, error_msg = validate_critical_fields(data, 'laptop')
        if not is_valid:
            return ErrorResponse(error=error_msg, details={"category": "laptop"})
        
        features = extract_and_prepare_features(data, 'laptop')
        features = compute_advanced_features(features, 'laptop')
        
        model, model_type = load_model('laptop')
        X = prepare_feature_array(features, 'laptop')
        predicted_price = float(model.predict(X)[0])
        
        completeness = sum([
            1 if features.get('ram') else 0,
            1 if features.get('storage') else 0,
            1 if features.get('processor_tier', 0) > 0 else 0,
            1 if features.get('gpu_tier', 0) > 0 else 0
        ]) / 4
        
        confidence = "high" if completeness > 0.75 else "medium" if completeness > 0.5 else "low"
        margin = 0.05 if confidence == "high" else 0.10
        
        return PredictionResponse(
            success=True,
            category="laptop",
            predicted_price=round(predicted_price, 2),
            confidence=confidence,
            price_range={
                "min": round(predicted_price * (1 - margin), 2),
                "max": round(predicted_price * (1 + margin), 2)
            },
            extracted_features={k: v for k, v in features.items() if k in ['brand_premium', 'ram', 'storage', 'processor_tier', 'gpu_tier', 'has_dedicated_gpu']},
            message=f"Price predicted successfully using {model_type} model with {confidence} confidence"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return ErrorResponse(error="Prediction failed", details={"message": str(e)})

@router.post("/furniture", response_model=Union[PredictionResponse, ErrorResponse])
async def predict_furniture_price(input_data: FurniturePredictionInput):
    """Predict furniture price with validation"""
    
    try:
        data = input_data.dict()
        
        is_valid, error_msg = validate_critical_fields(data, 'furniture')
        if not is_valid:
            return ErrorResponse(error=error_msg, details={"category": "furniture"})
        
        features = extract_and_prepare_features(data, 'furniture')
        features = compute_advanced_features(features, 'furniture')
        
        model, model_type = load_model('furniture')
        X = prepare_feature_array(features, 'furniture')
        predicted_price = float(model.predict(X)[0])
        
        completeness = sum([
            1 if features.get('material_quality', 0) > 0 else 0,
            1 if features.get('furniture_type', 0) > 0 else 0,
            1 if features.get('volume', 0) > 0 else 0,
            1 if data.get('material') else 0
        ]) / 4
        
        confidence = "high" if completeness > 0.75 else "medium" if completeness > 0.5 else "low"
        margin = 0.05 if confidence == "high" else 0.10
        
        return PredictionResponse(
            success=True,
            category="furniture",
            predicted_price=round(predicted_price, 2),
            confidence=confidence,
            price_range={
                "min": round(predicted_price * (1 - margin), 2),
                "max": round(predicted_price * (1 + margin), 2)
            },
            extracted_features={k: v for k, v in features.items() if k in ['material_quality', 'material_type', 'furniture_type', 'volume', 'seating_capacity', 'is_imported']},
            message=f"Price predicted successfully using {model_type} model with {confidence} confidence"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return ErrorResponse(error="Prediction failed", details={"message": str(e)})

@router.get("/health")
async def health_check():
    """Check if models are loaded"""
    status = {}
    for category in ['mobile', 'laptop', 'furniture']:
        try:
            load_model(category)
            status[category] = "ready"
        except:
            status[category] = "not_available"
    
    return {"status": "healthy", "models": status}
