"""Test script to verify the ultimate model works with predictions endpoint"""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Load the model
model_path = Path('ml_models/price_predictor_mobiles.pkl')
model = joblib.load(model_path)

print("Model loaded successfully!")
print(f"Model type: {type(model)}")

# Create sample data matching training format
sample_data = pd.DataFrame([{
    'Title': 'iPhone 14 Pro 256GB',
    'Brand': 'Apple',
    'Condition': 'new',
    'ram_gb': 6,
    'storage_gb': 256,
    'camera_mp': 48,
    'battery_mah': 3200,
    'screen_inch': 6.1,
    'has_5g': 1,
    'year': 2023,
    'ram_storage_ratio': 6/256,
    'spec_score': 0.85,
    'age': 1,
    'age_factor': 0.95,
    'brand_tier': 'Premium',
    'brand_avg_price': 80000,
    'flagship_score': 2,
    'title_length': 20,
    'title_words': 4,
    'condition_score': 6
}])

print("\nSample data:")
print(sample_data.head())

try:
    # Make prediction
    prediction = model.predict(sample_data)
    print(f"\n✓ Prediction successful: PKR {prediction[0]:,.0f}")
except Exception as e:
    print(f"\n✗ Prediction failed: {e}")
    print(f"\nExpected features by model:")
    if hasattr(model, 'feature_names_in_'):
        print(model.feature_names_in_)
