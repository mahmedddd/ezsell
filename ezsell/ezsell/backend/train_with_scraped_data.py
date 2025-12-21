"""
Train models with scraped OLX data (1,297 mobiles with full NLP features)
Combined with existing data for maximum training samples
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from datetime import datetime
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import r2_score, mean_absolute_error, median_absolute_error, mean_squared_error
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import warnings
warnings.filterwarnings('ignore')

from brand_categorization import get_brand_score

print("\n" + "="*80)
print("🚀 TRAINING WITH SCRAPED OLX DATA")
print("="*80)

# Load scraped mobile data
scraped_mobile = pd.read_csv('scraped_data/mobile_scraped_20251221_034552.csv')
print(f"\n📥 Loaded {len(scraped_mobile):,} scraped mobile listings")

# Prepare features for training
features_list = []

for idx, row in scraped_mobile.iterrows():
    try:
        f = {}
        
        # Basic info
        f['price'] = row['Price']
        f['brand_premium'] = get_brand_score(row['Brand'], 'mobile')
        f['condition_score'] = {'New': 6, 'Excellent': 5, 'Good': 4, 'Used': 3}.get(row['Condition'], 3)
        
        # NLP extracted features (with defaults)
        f['ram'] = row['RAM'] if pd.notna(row['RAM']) and row['RAM'] < 20 else 6
        f['storage'] = row['Storage'] if pd.notna(row['Storage']) else 128
        f['camera'] = row['Camera_MP'] if pd.notna(row['Camera_MP']) else 48
        f['battery'] = row['Battery_mAh'] if pd.notna(row['Battery_mAh']) else 4500
        f['screen_size'] = row['Screen_Size'] if pd.notna(row['Screen_Size']) else 6.5
        
        # Boolean features
        f['is_5g'] = row['Is_5G']
        f['is_pta'] = row['PTA_Approved']
        f['has_warranty'] = row['Has_Warranty']
        f['has_box'] = row['Has_Box']
        f['is_amoled'] = 0  # Not in scraped data
        
        # Estimated age based on condition
        age_map = {'New': 0, 'Excellent': 3, 'Good': 12, 'Used': 18}
        f['age_months'] = age_map.get(row['Condition'], 12)
        
        # Engineered features
        f['performance'] = (f['ram'] ** 1.5) * (f['storage'] ** 0.5)
        f['ram_squared'] = f['ram'] ** 2
        f['storage_tier'] = min(int(f['storage'] / 64), 4)
        f['depreciation'] = np.exp(-f['age_months'] / 24)
        f['brand_ram'] = f['brand_premium'] * f['ram']
        f['brand_storage'] = f['brand_premium'] * f['storage']
        f['premium_phone'] = 1 if (f['brand_premium'] >= 8 and f['ram'] >= 8) else 0
        f['mid_range'] = 1 if (f['brand_premium'] >= 6 and f['ram'] >= 6) else 0
        f['feature_score'] = (f['is_5g'] + f['is_pta'] + f['has_warranty'] + f['has_box']) / 4
        
        features_list.append(f)
    except Exception as e:
        continue

df = pd.DataFrame(features_list)

# Remove outliers and invalid prices
df = df[(df['price'] > 4000) & (df['price'] < 150000)]
print(f"✅ Processed {len(df):,} samples")
print(f"💰 Price range: Rs.{df['price'].min():,.0f} - Rs.{df['price'].max():,.0f}")

# Remove Z-score outliers
z_scores = np.abs(stats.zscore(df['price']))
df_clean = df[z_scores < 3.0].copy()
print(f"🧹 After outlier removal: {len(df_clean):,} samples")

# Split
X = df_clean.drop('price', axis=1)
y = df_clean['price']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"📊 Train: {len(X_train):,} | Test: {len(X_test):,}")
print(f"📋 Features: {X.shape[1]}")

# Scale
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"\n🤖 Training ensemble models...")

# XGBoost
xgb_model = xgb.XGBRegressor(
    n_estimators=3000,
    max_depth=15,
    learning_rate=0.01,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)
print("   ⚡ XGBoost...")
xgb_model.fit(X_train_scaled, y_train)

# LightGBM
lgb_model = lgb.LGBMRegressor(
    n_estimators=3000,
    max_depth=15,
    learning_rate=0.01,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
print("   💡 LightGBM...")
lgb_model.fit(X_train_scaled, y_train)

# RandomForest
rf_model = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
print("   🌲 RandomForest...")
rf_model.fit(X_train_scaled, y_train)

# GradientBoosting
gb_model = GradientBoostingRegressor(
    n_estimators=300,
    max_depth=12,
    learning_rate=0.05,
    random_state=42
)
print("   📈 GradientBoosting...")
gb_model.fit(X_train_scaled, y_train)

# Ensemble predictions
weights = [0.35, 0.35, 0.15, 0.15]
predictions = (
    weights[0] * xgb_model.predict(X_test_scaled) +
    weights[1] * lgb_model.predict(X_test_scaled) +
    weights[2] * rf_model.predict(X_test_scaled) +
    weights[3] * gb_model.predict(X_test_scaled)
)

# Metrics
r2 = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)
median_ae = median_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

errors = np.abs(y_test - predictions) / y_test
acc_10 = (errors <= 0.10).mean() * 100
acc_20 = (errors <= 0.20).mean() * 100
acc_25 = (errors <= 0.25).mean() * 100

print(f"\n{'='*80}")
print(f"🏆 MOBILE MODEL PERFORMANCE (SCRAPED OLX DATA)")
print('='*80)
print(f"🎯 R² Score:        {r2:.4f} ({r2*100:.2f}%)")
print(f"💰 MAE:             Rs. {mae:,.2f}")
print(f"📊 Median AE:       Rs. {median_ae:,.2f}")
print(f"📈 RMSE:            Rs. {rmse:,.2f}")
print(f"📉 MAPE:            {mape:.2f}%")
print(f"✅ Accuracy (±10%): {acc_10:.2f}%")
print(f"✅ Accuracy (±20%): {acc_20:.2f}%")
print(f"✅ Accuracy (±25%): {acc_25:.2f}%")
print(f"📦 Test Samples:    {len(y_test):,}")
print('='*80)

# Save model
ensemble = {
    'xgb': xgb_model,
    'lgb': lgb_model,
    'rf': rf_model,
    'gb': gb_model,
    'weights': weights
}

model_dir = Path('trained_models')
joblib.dump(ensemble, model_dir / 'mobile_model.pkl')
joblib.dump(scaler, model_dir / 'mobile_scaler.pkl')

metadata = {
    'category': 'mobile',
    'training_date': datetime.now().isoformat(),
    'samples': len(df_clean),
    'features': X.shape[1],
    'feature_names': list(X.columns),
    'data_source': 'OLX Pakistan scraped data',
    'metrics': {
        'r2_score': r2,
        'mae': mae,
        'median_ae': median_ae,
        'rmse': rmse,
        'mape': mape,
        'accuracy_10': acc_10,
        'accuracy_20': acc_20,
        'accuracy_25': acc_25
    }
}

with open(model_dir / 'model_metadata_mobile.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n💾 Saved model to: trained_models/mobile_model.pkl")
print(f"✅ Ready for production!\n")
