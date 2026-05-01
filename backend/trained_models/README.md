# 🎯 Production-Ready Price Prediction Models

## Overview
High-accuracy regression models for price prediction across 3 categories using ensemble learning (XGBoost + LightGBM + RandomForest + GradientBoosting).

## Model Performance

### 📱 Mobile Model
- **R² Score**: 86.78% (Production Ready ✅)
- **MAE**: Rs. 4,535
- **Median Error**: Rs. 2,532
- **MAPE**: 13.28%
- **Accuracy (±20%)**: 79.28%
- **Accuracy (±25%)**: 87.63%
- **Test Samples**: 994

### 💻 Laptop Model
- **R² Score**: 93.16% (Production Ready ✅)
- **MAE**: Rs. 4,120
- **Median Error**: Rs. 2,771
- **MAPE**: 12.43%
- **Accuracy (±10%)**: 60.17%
- **Accuracy (±20%)**: 84.75%
- **Accuracy (±25%)**: 91.53%
- **Test Samples**: 118

### 🪑 Furniture Model
- **R² Score**: 92.95% (Production Ready ✅)
- **MAE**: Rs. 3,560
- **Median Error**: Rs. 2,769
- **MAPE**: 24.95%
- **Accuracy (±20%)**: 66.89%
- **Accuracy (±25%)**: 79.05%
- **Test Samples**: 148

## Model Files

### Mobile
- `mobile_model.pkl` (68.67 MB) - Trained ensemble model
- `mobile_scaler.pkl` - Feature scaler
- `mobile_metadata.json` - Model metadata and metrics

### Laptop
- `laptop_model.pkl` (37.82 MB) - Trained ensemble model
- `laptop_scaler.pkl` - Feature scaler
- `laptop_metadata.json` - Model metadata and metrics

### Furniture
- `furniture_model.pkl` (21.57 MB) - Trained ensemble model
- `furniture_scaler.pkl` - Feature scaler
- `furniture_metadata.json` - Model metadata and metrics

## Usage

```python
import joblib
import pandas as pd
import numpy as np

# Load model and scaler
model = joblib.load('trained_models/mobile_model.pkl')
scaler = joblib.load('trained_models/mobile_scaler.pkl')

# Prepare features (example for mobile)
features = pd.DataFrame({
    'brand_premium': [8],
    'ram': [8],
    'storage': [128],
    'battery': [5000],
    'camera': [48],
    'screen_size': [6.5],
    'is_5g': [1],
    'is_pta': [1],
    'is_amoled': [1],
    'has_warranty': [1],
    'has_box': [1],
    'condition_score': [9],
    'age_months': [2],
    # ... additional engineered features
})

# Scale features
features_scaled = scaler.transform(features)

# Predict
prediction = model['xgb'].predict(features_scaled)  # Use ensemble
# Or use weighted prediction from all models

print(f"Predicted Price: Rs. {prediction[0]:,.2f}")
```

## Model Architecture

**Ensemble Composition:**
- XGBoost (35% weight) - 2000 estimators, max_depth=12
- LightGBM (35% weight) - 2000 estimators, max_depth=15
- RandomForest (15% weight) - 500 estimators, max_depth=20
- GradientBoosting (15% weight) - 800 estimators, max_depth=10

**Training Details:**
- Stratified train-test split (80/20)
- Outlier removal (Z-score < 2.5)
- RobustScaler for feature scaling
- Price-based feature engineering
- Polynomial and interaction features

## Feature Sets

### Mobile (24 features)
Base: brand_premium, ram, storage, battery, camera, screen_size, is_5g, is_pta, is_amoled, has_warranty, has_box, condition_score, age_months

Engineered: performance, ram_storage, ram_squared, camera_tier, battery_tier, premium_count, depreciation, brand_ram, price_category, polynomial features

### Laptop (23 features)
Base: brand_premium, processor_tier, generation, ram, storage, has_gpu, gpu_tier, is_gaming, is_touchscreen, has_ssd, screen_size, condition_score, age_months

Engineered: cpu_score, gaming_score, memory_score, ram_squared, ssd_value, depreciation, price_category, polynomial features

### Furniture (21 features)
Base: material_quality, seating_capacity, length, width, height, volume, is_imported, is_handmade, has_storage, is_modern, is_antique, condition_score

Engineered: volume_log, size_tier, quality, seating_value, premium_count, price_category, polynomial features

## Training Data
- **Mobile**: 4,966 samples (after outlier removal)
- **Laptop**: 586 samples (after outlier removal)
- **Furniture**: 740 samples (after outlier removal)

## Last Trained
December 13, 2025

## Notes
- Models use ensemble predictions (weighted average of 4 algorithms)
- Price predictions are capped at minimum 0 (no negative prices)
- Best performance on Laptop category (93.16% R²)
- All models exceed 80% R² threshold for production use
