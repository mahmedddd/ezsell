# 🎯 Quick Reference - Production Models

## Model Files (Use These for Predictions)

```
trained_models/
├── mobile_model.pkl      # 68.67 MB - Mobile price predictor (86.78% R²)
├── mobile_scaler.pkl     # Feature scaler for mobile
├── laptop_model.pkl      # 37.82 MB - Laptop price predictor (93.16% R²)
├── laptop_scaler.pkl     # Feature scaler for laptop
├── furniture_model.pkl   # 21.57 MB - Furniture price predictor (92.95% R²)
└── furniture_scaler.pkl  # Feature scaler for furniture
```

## Quick Load Example

```python
import joblib

# Load mobile model
mobile_model = joblib.load('trained_models/mobile_model.pkl')
mobile_scaler = joblib.load('trained_models/mobile_scaler.pkl')

# Load laptop model
laptop_model = joblib.load('trained_models/laptop_model.pkl')
laptop_scaler = joblib.load('trained_models/laptop_scaler.pkl')

# Load furniture model
furniture_model = joblib.load('trained_models/furniture_model.pkl')
furniture_scaler = joblib.load('trained_models/furniture_scaler.pkl')
```

## Model Structure

Each model is a dictionary containing:
- `'xgb'` - XGBoost model (35% weight)
- `'lgb'` - LightGBM model (35% weight)
- `'rf'` - RandomForest model (15% weight)
- `'gb'` - GradientBoosting model (15% weight)
- `'weights'` - [0.35, 0.35, 0.15, 0.15]

## Prediction Template

```python
import pandas as pd

# 1. Prepare features
features = pd.DataFrame([{
    'feature1': value1,
    'feature2': value2,
    # ... all required features
}])

# 2. Scale features
scaled_features = scaler.transform(features)

# 3. Get predictions from all models
pred_xgb = model['xgb'].predict(scaled_features)[0]
pred_lgb = model['lgb'].predict(scaled_features)[0]
pred_rf = model['rf'].predict(scaled_features)[0]
pred_gb = model['gb'].predict(scaled_features)[0]

# 4. Weighted ensemble
weights = model['weights']
predictions = [pred_xgb, pred_lgb, pred_rf, pred_gb]
final_price = sum(w * p for w, p in zip(weights, predictions))

# 5. Ensure positive price
final_price = max(0, final_price)
```

## Required Features

### Mobile (24 features)
```python
{
    # Base features (13)
    'brand_premium': 8,        # 1-10 scale
    'ram': 8,                  # GB
    'storage': 128,            # GB
    'battery': 5000,           # mAh
    'camera': 48,              # MP
    'screen_size': 6.5,        # inches
    'is_5g': 1,                # 0 or 1
    'is_pta': 1,               # 0 or 1
    'is_amoled': 1,            # 0 or 1
    'has_warranty': 1,         # 0 or 1
    'has_box': 1,              # 0 or 1
    'condition_score': 9,      # 1-10 scale
    'age_months': 2,           # months
    
    # Engineered features (11)
    'price_category': 4,       # 1-5 bin
    'performance': 128.0,      # calculated
    'ram_storage': 1024,       # ram * storage
    'ram_squared': 64,         # ram^2
    'camera_tier': 4,          # 1-5 tier
    'battery_tier': 3,         # 1-5 tier
    'premium_count': 5,        # sum of boolean features
    'depreciation': 0.95,      # exp(-age/24)
    'brand_ram': 64,           # brand * ram
    # ... polynomial features
}
```

### Laptop (23 features)
```python
{
    # Base features (13)
    'brand_premium': 9,
    'processor_tier': 7,       # 1-10 (i3=3, i5=5, i7=7, i9=9)
    'generation': 12,          # CPU generation
    'ram': 16,
    'storage': 512,
    'has_gpu': 1,
    'gpu_tier': 6,             # 1-10
    'is_gaming': 1,
    'is_touchscreen': 0,
    'has_ssd': 1,
    'screen_size': 15.6,
    'condition_score': 9,
    'age_months': 6,
    
    # Engineered features (10)
    'price_category': 4,
    'cpu_score': 84,           # tier * generation
    'gaming_score': 36,        # gpu_tier^2
    'memory_score': 2048,      # calculated
    'ram_squared': 256,
    'ssd_value': 512,          # has_ssd * storage
    'depreciation': 0.87,
    # ... polynomial features
}
```

### Furniture (21 features)
```python
{
    # Base features (12)
    'material_quality': 8,     # 1-10
    'seating_capacity': 5,     # number of seats
    'length': 180,             # cm
    'width': 90,               # cm
    'height': 85,              # cm
    'volume': 1377000,         # cm³
    'is_imported': 1,
    'is_handmade': 0,
    'has_storage': 1,
    'is_modern': 1,
    'is_antique': 0,
    'condition_score': 8,
    
    # Engineered features (9)
    'price_category': 3,
    'volume_log': 14.1,        # log(volume)
    'size_tier': 3,            # 1-5
    'quality': 64,             # material * condition
    'seating_value': 11.2,     # capacity^1.5
    'premium_count': 2,
    # ... polynomial features
}
```

## Accuracy Metrics

| Model | R² | MAE | MAPE | ±10% | ±20% | ±25% |
|-------|-----|-----|------|------|------|------|
| 📱 Mobile | 86.78% | ₨4,535 | 13.28% | 47% | 79% | 88% |
| 💻 Laptop | 93.16% | ₨4,120 | 12.43% | 60% | 85% | 92% |
| 🪑 Furniture | 92.95% | ₨3,560 | 24.95% | 32% | 67% | 79% |

## Status
✅ All models production-ready (>80% R²)  
✅ Saved as: `mobile_model.pkl`, `laptop_model.pkl`, `furniture_model.pkl`  
✅ Ready for API integration
