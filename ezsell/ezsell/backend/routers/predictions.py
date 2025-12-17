# AI-powered price prediction endpoints
from fastapi import APIRouter, HTTPException
import joblib
import numpy as np
import pandas as pd
import re
from pathlib import Path

from schemas.schemas import PricePredictionRequest, PricePredictionResponse

router = APIRouter()

# Feature extraction functions (matching training)
def extract_ram(text):
    if not text:
        return 4
    text = str(text).lower()
    ram_match = re.search(r'(\d+)\s*gb\s+ram', text)
    if ram_match:
        ram = int(ram_match.group(1))
        if ram in [2, 3, 4, 6, 8, 12, 16]:
            return ram
    slash_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*gb', text)
    if slash_match:
        potential_ram = int(slash_match.group(1))
        if potential_ram in [2, 3, 4, 6, 8, 12, 16]:
            return potential_ram
    for ram_size in [16, 12, 8, 6, 4, 3, 2]:
        if f'{ram_size}gb' in text.replace(' ', ''):
            if not re.search(f'{ram_size}gb.*?(128|256|512)', text):
                return ram_size
    return 4

def extract_storage(text):
    if not text:
        return 64
    text = str(text).lower()
    tb_match = re.search(r'(\d+)\s*tb', text)
    if tb_match:
        return int(tb_match.group(1)) * 1024
    slash_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*gb', text)
    if slash_match:
        potential_storage = int(slash_match.group(2))
        if potential_storage in [16, 32, 64, 128, 256, 512, 1024]:
            return potential_storage
    storage_match = re.search(r'(\d+)\s*gb\s*(?:storage|rom|internal)', text)
    if storage_match:
        storage = int(storage_match.group(1))
        if storage in [16, 32, 64, 128, 256, 512, 1024]:
            return storage
    for size in [1024, 512, 256, 128, 64, 32, 16]:
        if f'{size}gb' in text.replace(' ', ''):
            return size
    return 64

def extract_camera(text):
    if not text:
        return 0
    text = str(text).lower()
    match = re.search(r'(\d+)\s*mp', text)
    if match:
        mp = int(match.group(1))
        if 2 <= mp <= 200:
            return mp
    return 0

def extract_battery(text):
    if not text:
        return 0
    text = str(text).lower()
    match = re.search(r'(\d{4,5})\s*mah', text)
    if match:
        mah = int(match.group(1))
        if 1000 <= mah <= 10000:
            return mah
    return 0

def extract_screen_size(text):
    if not text:
        return 0
    text = str(text).lower()
    match = re.search(r'(\d+\.?\d*)\s*(?:inch|")', text)
    if match:
        size = float(match.group(1))
        if 3.0 <= size <= 8.0:
            return size
    return 0

def is_5g(text):
    if not text:
        return 0
    return 1 if '5g' in str(text).lower() else 0

def extract_year(text):
    if not text:
        return 2023
    match = re.search(r'20(1[5-9]|2[0-5])', str(text))
    if match:
        return int(match.group(0))
    return 2023

def get_brand_tier(brand):
    if not brand:
        return 'Mid'
    brand = str(brand).lower()
    premium = ['apple', 'samsung', 'google', 'sony', 'huawei']
    upper_mid = ['oneplus', 'oppo', 'vivo', 'xiaomi', 'realme', 'motorola', 'nokia']
    budget = ['infinix', 'tecno', 'itel', 'redmi', 'poco']
    for p in premium:
        if p in brand:
            return 'Premium'
    for u in upper_mid:
        if u in brand:
            return 'Upper-Mid'
    for b in budget:
        if b in brand:
            return 'Budget'
    return 'Mid'

def is_flagship_keyword(text):
    if not text:
        return 0
    text = str(text).lower()
    keywords = ['pro', 'ultra', 'max', 'plus', 'flagship', 'premium', 'edge']
    return sum(1 for k in keywords if k in text)

def condition_to_score(condition):
    if not condition:
        return 3
    condition = str(condition).lower()
    mapping = {
        'new': 6, 'brand new': 6, 'excellent': 5, 'very good': 4,
        'good': 3, 'fair': 2, 'poor': 1
    }
    for key, value in mapping.items():
        if key in condition:
            return value
    return 3

# Load pre-trained models
models_path = Path(__file__).parent.parent / "trained_models"

# Cache loaded models and metadata
_loaded_models = {}
_loaded_metadata = {}

def load_model(category: str):
    """Load the appropriate model for the category"""
    # Map category names to model file names
    category_map = {
        "mobile": "mobile",
        "laptop": "laptop",
        "furniture": "furniture"
    }
    
    model_name = category_map.get(category.lower())
    if not model_name:
        return None, None
    
    # Return cached model if available
    if model_name in _loaded_models:
        return _loaded_models[model_name], _loaded_metadata.get(model_name)
    
    try:
        model_file = models_path / f"{model_name}_model.pkl"
        metadata_file = models_path / f"{model_name}_metadata.json"
        
        if model_file.exists():
            model = joblib.load(model_file)
            _loaded_models[model_name] = model
            
            # Load metadata if available
            metadata = None
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                _loaded_metadata[model_name] = metadata
            
            return model, metadata
        return None, None
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

@router.post("/predict-price", response_model=PricePredictionResponse)
def predict_price(request: PricePredictionRequest):
    """Predict the optimal price for an item based on its features"""
    
    category = request.category.lower()
    features = request.features
    
    # Validate category
    if category not in ["mobile", "laptop", "furniture"]:
        raise HTTPException(status_code=400, detail="Invalid category. Must be 'mobile', 'laptop', or 'furniture'")
    
    # Validate required fields based on category
    required_fields = {
        "mobile": ["title", "condition", "brand"],
        "laptop": ["title", "condition", "brand"],
        "furniture": ["title", "condition"]
    }
    
    missing_fields = []
    for field in required_fields[category]:
        if not features.get(field) or str(features.get(field)).strip() == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required fields for {category}: {', '.join(missing_fields)}. Please provide all required information."
        )
    
    # Load model
    model, metadata = load_model(category)
    
    if not model:
        raise HTTPException(
            status_code=503, 
            detail=f"Price prediction model for {category} is not available. Please train the model first."
        )
    
    # Get confidence from metadata or use default
    confidence = 0.75  # Default confidence
    if metadata and 'test_r2' in metadata:
        # Convert R² to confidence percentage (0-1 scale)
        confidence = min(max(metadata['test_r2'], 0.5), 0.95)  # Clamp between 50-95%
    
    # Use actual model for prediction
    try:
        # Prepare input DataFrame matching training data format
        if category == "mobile":
            title = features.get('title', '')
            brand = features.get('brand', 'Unknown')
            condition = features.get('condition', 'good')
            
            # Extract features matching train_models.py preprocessing
            ram = extract_ram(title)
            storage = extract_storage(title)
            camera = extract_camera(title)
            battery = extract_battery(title)
            screen_size = extract_screen_size(title)
            has_5g_flag = is_5g(title)
            condition_score_val = condition_to_score(condition)
            
            # Brand premium (1-10)
            brands = {'samsung': 8, 'apple': 10, 'iphone': 10, 'xiaomi': 6, 'oppo': 5, 'vivo': 5,
                     'realme': 5, 'oneplus': 8, 'huawei': 7, 'honor': 6, 'nokia': 4}
            brand_premium = 5
            for brand_name, score in brands.items():
                if brand_name in brand.lower():
                    brand_premium = score
                    break
            
            # Boolean features
            is_pta = 1 if 'pta' in title.lower() else 0
            is_amoled = 1 if 'amoled' in title.lower() else 0
            has_warranty = 1 if 'warranty' in title.lower() else 0
            has_box = 1 if 'box' in title.lower() else 0
            age_months = 6  # Default
            
            # Price category (estimate based on condition and specs)
            price_category = 3  # Mid-range default
            if brand_premium >= 8:
                price_category = 4
            elif brand_premium <= 4:
                price_category = 2
            
            # Create DataFrame with exact features from training
            df = pd.DataFrame([{
                'brand_premium': brand_premium,
                'ram': ram,
                'storage': storage,
                'battery': battery,
                'camera': camera,
                'screen_size': screen_size,
                'is_5g': has_5g_flag,
                'is_pta': is_pta,
                'is_amoled': is_amoled,
                'has_warranty': has_warranty,
                'has_box': has_box,
                'condition_score': condition_score_val,
                'age_months': age_months,
                'price_category': price_category
            }])
            
            # Engineer features matching train_models.py
            df['performance'] = (df['ram'] ** 1.5) * (df['storage'] ** 0.5)
            df['ram_squared'] = df['ram'] ** 2
            df['depreciation'] = np.exp(-df['age_months'] / 24)
            df['brand_ram'] = df['brand_premium'] * df['ram']
            
            # Save for response
            extracted_features = {
                "ram": ram,
                "storage": storage,
                "camera": camera if camera > 0 else "Not detected",
                "battery": battery if battery > 0 else "Not detected",
                "screen_size": screen_size if screen_size > 0 else "Not detected",
                "has_5g": bool(has_5g_flag),
                "brand_premium": brand_premium,
                "condition_score": condition_score_val
            }
        elif category == "laptop":
            title = features.get('title', '')
            description = features.get('description', '')
            brand = features.get('brand', 'Unknown')
            condition = features.get('condition', 'good')
            combined_text = f"{title} {description}"
            
            # Feature engineering matching training
            title_length = len(title)
            title_words = len(title.split())
            title_numbers = len(re.findall(r'\d+', title))
            desc_length = len(description)
            desc_words = len(description.split())
            desc_numbers = len(re.findall(r'\d+', description))
            
            # Quality score
            quality_score = len(description) * 0.1
            if any(word in description.lower() for word in ['new', 'excellent', 'warranty', 'original']):
                quality_score += 10
            quality_score = min(quality_score, 100)
            
            # Condition score
            condition_map = {'poor': 1, 'fair': 2, 'good': 3, 'very good': 4, 'excellent': 5, 'new': 6}
            condition_score_val = condition_map.get(condition.lower(), 3)
            
            # Brand popularity (simplified)
            popular_brands = ['hp', 'dell', 'lenovo', 'asus', 'acer', 'apple', 'microsoft']
            brand_popularity = 1 if any(b in brand.lower() for b in popular_brands) else 0
            
            df = pd.DataFrame([{
                'Title': title,
                'Brand': brand,
                'Condition': condition,
                'Description': description,
                'combined_text': combined_text,
                'title_length': title_length,
                'title_words': title_words,
                'title_numbers': title_numbers,
                'desc_length': desc_length,
                'desc_words': desc_words,
                'desc_numbers': desc_numbers,
                'quality_score': quality_score,
                'condition_score': condition_score_val,
                'brand_popularity': brand_popularity
            }])
        elif category == "furniture":
            title = features.get('title', '')
            description = features.get('description', '')
            condition = features.get('condition', 'good')
            furniture_type = features.get('type', 'Unknown')
            material = features.get('material', 'Unknown')
            combined_text = f"{title} {description}"
            
            # Feature engineering matching training
            title_length = len(title)
            title_words = len(title.split())
            title_numbers = len(re.findall(r'\d+', title))
            desc_length = len(description)
            desc_words = len(description.split())
            desc_numbers = len(re.findall(r'\d+', description))
            
            # Quality score
            quality_score = len(description) * 0.1
            if any(word in description.lower() for word in ['new', 'excellent', 'warranty', 'original']):
                quality_score += 10
            quality_score = min(quality_score, 100)
            
            # Condition score
            condition_map = {'poor': 1, 'fair': 2, 'good': 3, 'very good': 4, 'excellent': 5, 'new': 6}
            condition_score_val = condition_map.get(condition.lower(), 3)
            
            # Brand/type popularity (simplified)
            popular_types = ['sofa', 'bed', 'table', 'chair', 'desk']
            brand_popularity = 1 if any(t in furniture_type.lower() for t in popular_types) else 0
            
            df = pd.DataFrame([{
                'Title': title,
                'Description': description,
                'Condition': condition,
                'Type': furniture_type,
                'Material': material,
                'combined_text': combined_text,
                'title_length': title_length,
                'title_words': title_words,
                'title_numbers': title_numbers,
                'desc_length': desc_length,
                'desc_words': desc_words,
                'desc_numbers': desc_numbers,
                'quality_score': quality_score,
                'condition_score': condition_score_val,
                'brand_popularity': brand_popularity
            }])
        
        # Drop non-numeric columns before prediction
        numeric_df = df.select_dtypes(include=[np.number])
        
        # Make prediction using ensemble
        if isinstance(model, dict):
            # Ensemble model with multiple estimators
            predictions = []
            weights = model.get('weights', [0.35, 0.35, 0.15, 0.15])
            
            for key, weight in zip(['xgb', 'lgb', 'rf', 'gb'], weights):
                if key in model:
                    pred = model[key].predict(numeric_df)[0]
                    predictions.append(pred * weight)
            
            predicted_price = float(sum(predictions))
        else:
            # Single model
            predicted_price = float(model.predict(numeric_df)[0])
        
        # Confidence already loaded from metadata above
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
    
    # Calculate price range (±15%)
    price_range_min = predicted_price * 0.85
    price_range_max = predicted_price * 1.15
    
    return PricePredictionResponse(
        predicted_price=round(predicted_price, 2),
        confidence_score=round(confidence, 2),
        price_range_min=round(price_range_min, 2),
        price_range_max=round(price_range_max, 2),
        extracted_features=extracted_features
    )

@router.get("/prediction-features/{category}")
def get_required_features(category: str):
    """Get the list of required features for a specific category"""
    features_map = {
        "mobile": {
            "required": ["title", "brand", "condition"],
            "optional": ["description"]
        },
        "laptop": {
            "required": ["title", "brand", "model", "condition"],
            "optional": ["type", "description"]
        },
        "furniture": {
            "required": ["title", "condition", "type"],
            "optional": ["description", "material"]
        }
    }
    
    if category.lower() not in features_map:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    return {"category": category, "features": features_map[category.lower()]}
