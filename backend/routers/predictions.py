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
        scaler_file = models_path / f"{model_name}_scaler.pkl"
        metadata_file = models_path / f"{model_name}_metadata.json"
        
        # Load metadata
        metadata = None
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            _loaded_metadata[model_name] = metadata
        
        # Load the trained model
        if model_file.exists():
            model = joblib.load(model_file)
            scaler = joblib.load(scaler_file) if scaler_file.exists() else None
            _loaded_models[model_name] = {'model': model, 'scaler': scaler}
            return _loaded_models[model_name], metadata
        else:
            print(f"Model file not found: {model_file}")
            return None, None
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

@router.post("/predict-price", response_model=PricePredictionResponse)
async def predict_price(request: PricePredictionRequest):
    """Predict the optimal price using Groq AI (prevents OOM crashes)"""
    from services.llm_pricing_service import llm_pricing_service
    
    category = request.category.lower()
    features = request.features
    
    # Extract basic info
    title = str(features.get('title', '')).strip()
    brand = str(features.get('brand', '')).strip()
    condition = str(features.get('condition', 'good')).strip()
    
    # Map condition to a 1-10 scale for the LLM
    condition_map = {
        'new': 10, 'brand new': 10, 'excellent': 8, 
        'very good': 7, 'good': 6, 'fair': 4, 'poor': 2
    }
    condition_score = condition_map.get(condition.lower(), 6)

    try:
        # Use Groq via LLMPricingService
        # This is fast, uses 0 RAM on our server, and is more accurate for the current market
        result = await llm_pricing_service.estimate_market_price(
            category=category,
            extracted_specs={},  # LLM will extract from title
            user_selections=features,
            condition=str(condition_score),
            title=title,
            dynamic_specs=features
        )
        
        predicted_price = float(result.get("estimated_price", 0))
        confidence = float(result.get("confidence", 0.75))
        
        # If LLM failed, use a very basic fallback to avoid 500 error
        if predicted_price == 0:
            if category == "mobile": predicted_price = 45000
            elif category == "laptop": predicted_price = 65000
            else: predicted_price = 15000

        # Adjust for condition manually as a safety multiplier
        # (The LLM is asked for price BEFORE condition, we apply it here)
        condition_multipliers = {10: 1.0, 8: 0.9, 7: 0.85, 6: 0.75, 4: 0.5, 2: 0.3}
        multiplier = condition_multipliers.get(condition_score, 0.75)
        final_price = predicted_price * multiplier

        # Calculate price range (±15%)
        price_range_min = final_price * 0.85
        price_range_max = final_price * 1.15
        
        return PricePredictionResponse(
            predicted_price=round(final_price, 2),
            confidence_score=round(confidence, 2),
            price_range_min=round(price_range_min, 2),
            price_range_max=round(price_range_max, 2),
            extracted_features=result.get("extracted_specs", features)
        )

    except Exception as e:
        print(f"Prediction error: {e}")
        # Final fallback to prevent crash
        return PricePredictionResponse(
            predicted_price=25000,
            confidence_score=0.5,
            price_range_min=20000,
            price_range_max=30000,
            extracted_features=features
        )

@router.get("/prediction-features/{category}")
def get_required_features(category: str):
    """Get the list of required features for a specific category"""
    features_map = {
        "mobile": {
            "required": ["title", "brand", "condition"],
            "optional": ["description"],
            "instructions": "Title must include RAM and storage specs (e.g., '6GB/128GB', '8GB RAM 256GB')"
        },
        "laptop": {
            "required": ["title", "brand", "model", "condition", "description"],
            "optional": ["type"],
            "instructions": "Description must include processor details (e.g., 'Intel Core i5', 'AMD Ryzen 7')"
        },
        "furniture": {
            "required": ["title", "condition", "type", "material"],
            "optional": ["description"],
            "furniture_types": [
                "Sofa", "Bed", "Dining Table", "Coffee Table", "Study Table", 
                "Office Desk", "Chair", "Office Chair", "Wardrobe", "Bookshelf",
                "TV Stand", "Dresser", "Cabinet", "Nightstand"
            ],
            "materials": [
                "Wood", "Solid Wood", "Engineered Wood", "Metal", "Steel",
                "Fabric", "Leather", "Faux Leather", "Plastic", "Glass",
                "Rattan", "Wicker", "Mixed Materials"
            ]
        }
    }
    
    if category.lower() not in features_map:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    return {"category": category, "features": features_map[category.lower()]}
