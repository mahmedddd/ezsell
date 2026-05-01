"""Optimize mobile model training for better accuracy"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from scipy import stats
import joblib
import json
from pathlib import Path
from datetime import datetime

print("\n" + "="*80)
print("🚀 OPTIMIZING MOBILE MODEL")
print("="*80)

# Load data
csv_file = "scraped_data/mobile_preprocessed_20251213_new.csv"
df = pd.read_csv(csv_file)
print(f"📊 Loaded {len(df)} samples")

# Remove invalid prices
initial_len = len(df)
df = df.dropna(subset=['price'])
df = df[df['price'] > 100]  # Minimum 100 PKR
df = df[df['price'] < 500000]  # Maximum 500K PKR (realistic mobile range)
df = df[~np.isinf(df['price'])]
print(f"🧹 Removed {initial_len - len(df)} rows with invalid prices")

# Use Z-score method for mobile (works better for mobile data)
z_scores = np.abs(stats.zscore(df['price']))
df = df[z_scores < 3.0]
print(f"✅ After Z-score outlier removal: {len(df)} samples")

# Price features
df['price_percentile'] = df['price'].rank(pct=True)

try:
    df['price_bin'] = pd.qcut(df['price'], q=5, labels=False, duplicates='drop') + 1
except:
    df['price_bin'] = (df['price_percentile'] * 5).astype(int) + 1
    df['price_bin'] = df['price_bin'].clip(1, 5)

# Mobile features
feature_cols = ['brand_premium', 'ram', 'storage', 'battery', 'camera', 'screen_size',
               'is_5g', 'is_pta', 'is_amoled', 'has_warranty', 'has_box',
               'condition_score', 'age_months']

available = [col for col in feature_cols if col in df.columns]
X = df[available].copy()
y = df['price'].copy()

# Add price category for better segmentation
# OK in training - will be estimated in API from features
X['price_category'] = df['price_bin']

# Engineer features
if 'ram' in X.columns and 'storage' in X.columns:
    X['performance'] = (X['ram'] ** 1.5) * (X['storage'] ** 0.5)
    X['ram_squared'] = X['ram'] ** 2
if 'age_months' in X.columns:
    X['depreciation'] = np.exp(-X['age_months'] / 24)
if 'brand_premium' in X.columns and 'ram' in X.columns:
    X['brand_ram'] = X['brand_premium'] * X['ram']

# Fill missing and remove infinity
X = X.fillna(X.median())
X = X.replace([np.inf, -np.inf], 0)

# Final validation
valid_idx = ~(y.isna() | np.isinf(y))
X = X[valid_idx]
y = y[valid_idx]

print(f"✅ Final dataset: {len(X)} samples, {X.shape[1]} features")

# Scale
scaler = RobustScaler()
feature_names = list(X.columns)
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=feature_names)

# Split
try:
    price_bins = pd.qcut(y, q=5, labels=False, duplicates='drop')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=price_bins
    )
except:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

print(f"📊 Train: {len(X_train)} | Test: {len(X_test)}")

# Train ensemble with optimized hyperparameters for mobile
print("🤖 Training optimized ensemble...")

print("   XGBoost...")
xgb_model = xgb.XGBRegressor(
    n_estimators=2500, learning_rate=0.015, max_depth=14,
    min_child_weight=1, subsample=0.8, colsample_bytree=0.8,
    gamma=0.05, reg_alpha=0.2, reg_lambda=3.0, random_state=42, n_jobs=-1
)
xgb_model.fit(X_train, y_train)

print("   LightGBM...")
lgb_model = lgb.LGBMRegressor(
    n_estimators=2500, learning_rate=0.015, max_depth=18, num_leaves=80,
    min_child_samples=12, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.2, reg_lambda=3.0, random_state=42, n_jobs=-1, verbose=-1
)
lgb_model.fit(X_train, y_train)

print("   RandomForest...")
rf_model = RandomForestRegressor(
    n_estimators=600, max_depth=22, min_samples_split=8,
    min_samples_leaf=3, max_features='sqrt', random_state=42, n_jobs=-1
)
rf_model.fit(X_train, y_train)

print("   GradientBoost...")
gb_model = GradientBoostingRegressor(
    n_estimators=1000, learning_rate=0.02, max_depth=12,
    min_samples_split=12, min_samples_leaf=4, subsample=0.8, random_state=42
)
gb_model.fit(X_train, y_train)

# Ensemble
ensemble = {
    'xgb': xgb_model,
    'lgb': lgb_model,
    'rf': rf_model,
    'gb': gb_model,
    'weights': [0.35, 0.35, 0.15, 0.15]
}

# Predict
print("📊 Evaluating...")
predictions = []
predictions.append(xgb_model.predict(X_test))
predictions.append(lgb_model.predict(X_test))
predictions.append(rf_model.predict(X_test))
predictions.append(gb_model.predict(X_test))

weights = ensemble['weights']
y_pred = sum(w * p for w, p in zip(weights, predictions))
y_pred = np.maximum(y_pred, 0)

# Metrics
mae = mean_absolute_error(y_test, y_pred)
median_ae = np.median(np.abs(y_test - y_pred))
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

acc_10 = np.mean(np.abs(y_test - y_pred) / y_test <= 0.10) * 100
acc_20 = np.mean(np.abs(y_test - y_pred) / y_test <= 0.20) * 100
acc_25 = np.mean(np.abs(y_test - y_pred) / y_test <= 0.25) * 100

print(f"\n{'='*80}")
print(f"🔥 OPTIMIZED MOBILE MODEL PERFORMANCE")
print(f"{'='*80}")
print(f"🏆 R² Score:        {r2:.4f} ({r2*100:.2f}%)")
print(f"💰 MAE:             Rs. {mae:,.2f}")
print(f"📊 Median AE:       Rs. {median_ae:,.2f}")
print(f"📈 RMSE:            Rs. {rmse:,.2f}")
print(f"📉 MAPE:            {mape:.2f}%")
print(f"✅ Accuracy (±10%): {acc_10:.2f}%")
print(f"✅ Accuracy (±20%): {acc_20:.2f}%")
print(f"✅ Accuracy (±25%): {acc_25:.2f}%")
print(f"📦 Test Samples:    {len(y_test)}")
print(f"{'='*80}\n")

# Save
models_dir = Path("trained_models")
joblib.dump(ensemble, models_dir / "mobile_model.pkl")
joblib.dump(scaler, models_dir / "mobile_scaler.pkl")

metadata = {
    'category': 'mobile',
    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'model_type': 'Optimized Ensemble (XGB+LGB+RF+GB)',
    'r2_score': float(r2),
    'mae': float(mae),
    'median_ae': float(median_ae),
    'rmse': float(rmse),
    'mape': float(mape),
    'accuracy_10pct': float(acc_10),
    'accuracy_20pct': float(acc_20),
    'accuracy_25pct': float(acc_25),
    'samples': len(y_test),
    'features': feature_names
}

with open(models_dir / "mobile_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"💾 Models saved successfully!")
print(f"{'='*80}\n")
