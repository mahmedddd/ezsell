"""
Complete ML Pipeline with Fixed Price Data
Fixes prices (multiply by 1000 where needed) and trains models to achieve >80% R² and accuracy
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
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

from brand_categorization import get_brand_score, get_material_score, get_condition_score, get_processor_tier, get_gpu_tier

# ============================================================================
# NLP FEATURE EXTRACTION
# ============================================================================

def extract_mobile_features(row):
    """Extract features from mobile listing"""
    title = str(row.get('Title', '')).lower()
    brand = str(row.get('Brand', '')).lower()
    condition = str(row.get('Condition', 'used')).lower()
    
    features = {}
    
    # Brand encoding
    features['brand_premium'] = get_brand_score(brand, 'mobile')
    
    # Extract RAM (8GB, 8/256, etc.) - more robust patterns
    ram_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*(?:gb|GB)', title)
    if ram_match:
        features['ram'] = int(ram_match.group(1))
        features['storage'] = int(ram_match.group(2))
    else:
        # Try RAM only
        ram_match = re.search(r'(\d+)\s*gb\s*ram', title)
        features['ram'] = int(ram_match.group(1)) if ram_match else 4
        
        # Try storage separately
        storage_match = re.search(r'(\d{2,4})\s*(?:gb|GB)(?!\s*ram)', title)
        features['storage'] = int(storage_match.group(1)) if storage_match else 64
    
    # Cap RAM at 16GB (anything higher is likely year like 2020)
    if features['ram'] > 16:
        features['ram'] = 4
    
    # Extract camera (MP)
    camera_match = re.search(r'(\d+)\s*mp', title)
    features['camera'] = int(camera_match.group(1)) if camera_match else 0
    
    # Extract battery (mAh)
    battery_match = re.search(r'(\d{4,5})\s*mah', title)
    features['battery'] = int(battery_match.group(1)) if battery_match else 4000
    
    # Extract screen size
    screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', title)
    features['screen_size'] = float(screen_match.group(1)) if screen_match else 6.0
    
    # Boolean features
    features['is_5g'] = 1 if '5g' in title else 0
    features['is_pta'] = 1 if 'pta' in title else 0
    features['is_amoled'] = 1 if 'amoled' in title else 0
    features['has_warranty'] = 1 if 'warranty' in title else 0
    features['has_box'] = 1 if 'box' in title else 0
    features['condition_score'] = get_condition_score(condition)
    
    # Age estimation
    features['age_months'] = 6 if condition == 'new' else 12
    
    return features

def extract_laptop_features(row):
    """Extract features from laptop listing"""
    title = str(row.get('Title', '')).lower()
    desc = str(row.get('Description', '')).lower()
    brand = str(row.get('Brand', '')).lower()
    condition = str(row.get('Condition', 'used')).lower()
    combined = title + ' ' + desc
    
    features = {}
    
    # Brand encoding
    features['brand_premium'] = get_brand_score(brand, 'laptop')
    
    # Processor tier
    features['processor_tier'] = get_processor_tier(combined)
    
    # Generation (for Intel)
    gen_match = re.search(r'(\d+)(?:th|nd|rd|st)?\s*gen', combined)
    features['generation'] = int(gen_match.group(1)) if gen_match else 8
    
    # RAM
    ram_match = re.search(r'(\d+)\s*gb\s*ram', combined)
    features['ram'] = int(ram_match.group(1)) if ram_match else 8
    
    # Storage
    storage_match = re.search(r'(\d{3,4})\s*gb', combined)
    features['storage'] = int(storage_match.group(1)) if storage_match else 512
    
    # GPU tier
    features['gpu_tier'] = get_gpu_tier(combined)
    
    # Boolean features
    features['is_gaming'] = 1 if any(word in combined for word in ['gaming', 'rtx', 'gtx']) else 0
    features['is_touchscreen'] = 1 if 'touch' in combined else 0
    features['has_ssd'] = 1 if 'ssd' in combined else 0
    
    # Screen size
    screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', combined)
    features['screen_size'] = float(screen_match.group(1)) if screen_match else 15.6
    
    features['condition_score'] = get_condition_score(condition)
    features['age_months'] = 6 if condition == 'new' else 18
    
    return features

def extract_furniture_features(row):
    """Extract features from furniture listing"""
    title = str(row.get('Title', '')).lower()
    desc = str(row.get('Description', '')).lower()
    material = str(row.get('Material', '')).lower()
    condition = str(row.get('Condition', 'good')).lower()
    combined = title + ' ' + desc
    
    features = {}
    
    # Material encoding
    features['material_quality'] = get_material_score(material)
    
    # Seating capacity
    seating_match = re.search(r'(\d+)\s*seater', combined)
    features['seating_capacity'] = int(seating_match.group(1)) if seating_match else 0
    
    # Dimensions (LxWxH)
    dim_match = re.search(r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+)', combined)
    if dim_match:
        features['length'] = int(dim_match.group(1))
        features['width'] = int(dim_match.group(2))
        features['height'] = int(dim_match.group(3))
    else:
        features['length'] = 100
        features['width'] = 50
        features['height'] = 80
    
    features['volume'] = features['length'] * features['width'] * features['height']
    
    # Boolean features
    features['is_imported'] = 1 if 'import' in combined else 0
    features['is_handmade'] = 1 if 'handmade' in combined or 'hand made' in combined else 0
    features['has_storage'] = 1 if 'storage' in combined else 0
    features['is_modern'] = 1 if 'modern' in combined else 0
    features['is_antique'] = 1 if 'antique' in combined or 'vintage' in combined else 0
    features['condition_score'] = get_condition_score(condition)
    
    return features

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================

def engineer_mobile_features(df):
    """Add engineered features for mobile"""
    df['performance'] = (df['ram'] ** 1.5) * (df['storage'] ** 0.5)
    df['ram_squared'] = df['ram'] ** 2
    df['storage_tier'] = pd.cut(df['storage'], bins=[0, 64, 128, 256, 2000], labels=[1,2,3,4]).astype(float)
    df['depreciation'] = np.exp(-df['age_months'] / 24)
    df['brand_ram'] = df['brand_premium'] * df['ram']
    df['brand_storage'] = df['brand_premium'] * df['storage']
    df['premium_phone'] = ((df['brand_premium'] >= 8) & (df['ram'] >= 8)).astype(int)
    df['mid_range'] = ((df['brand_premium'] >= 6) & (df['ram'] >= 6)).astype(int)
    df['feature_score'] = (df['is_5g'] + df['is_amoled'] + df['is_pta'] + df['has_warranty']) / 4
    
    # NO PRICE_CATEGORY - causes data leakage (0.87 correlation)
    
    return df

def engineer_laptop_features(df):
    """Add engineered features for laptop"""
    df['cpu_score'] = df['processor_tier'] * df['generation']
    df['memory_score'] = (df['ram'] ** 1.5) * (df['storage'] ** 0.3)
    df['gaming_score'] = (df['gpu_tier'] ** 2) * df['is_gaming']
    df['depreciation'] = np.exp(-df['age_months'] / 36)
    df['brand_cpu'] = df['brand_premium'] * df['processor_tier']
    df['premium_laptop'] = ((df['brand_premium'] >= 7) & (df['processor_tier'] >= 7)).astype(int)
    df['workstation'] = ((df['ram'] >= 16) & (df['processor_tier'] >= 7)).astype(int)
    
    # NO PRICE_CATEGORY - causes data leakage (0.92 correlation)
    
    return df

def engineer_furniture_features(df):
    """Add engineered features for furniture"""
    df['volume_log'] = np.log1p(df['volume'])
    df['size_tier'] = pd.cut(df['length'], bins=5, labels=[1,2,3,4,5]).astype(float)
    df['quality'] = df['material_quality'] * df['condition_score']
    df['seating_value'] = df['seating_capacity'] * df['material_quality']
    df['premium_material'] = (df['material_quality'] >= 7).astype(int)
    df['large_furniture'] = (df['volume'] > df['volume'].median()).astype(int)
    
    # NO PRICE_CATEGORY - causes data leakage (0.95 correlation)
    
    return df

# ============================================================================
# TRAINING
# ============================================================================

def train_model(df, category, outlier_method='zscore'):
    """Train ensemble model"""
    print(f"\n{'='*80}")
    print(f"🔥 TRAINING {category.upper()} MODEL")
    print('='*80)
    
    # Remove outliers
    if outlier_method == 'zscore':
        z_scores = np.abs(stats.zscore(df['price']))
        df_clean = df[z_scores < 3.0].copy()
    else:
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        df_clean = df[(df['price'] >= Q1 - 2.5*IQR) & (df['price'] <= Q3 + 2.5*IQR)].copy()
    
    print(f"🧹 Outliers removed: {len(df) - len(df_clean)}, retained: {len(df_clean):,}")
    
    # Split features and target
    X = df_clean.drop('price', axis=1)
    y = df_clean['price']
    
    print(f"✅ Training data: {len(X):,} samples, {X.shape[1]} features")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"📊 Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    # Scale features
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n🤖 Training ensemble models...")
    
    # XGBoost - Higher estimators for better learning
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
    
    # Weighted ensemble predictions
    weights = [0.35, 0.35, 0.15, 0.15]  # XGB, LGB, RF, GB
    
    predictions = (
        weights[0] * xgb_model.predict(X_test_scaled) +
        weights[1] * lgb_model.predict(X_test_scaled) +
        weights[2] * rf_model.predict(X_test_scaled) +
        weights[3] * gb_model.predict(X_test_scaled)
    )
    
    # Calculate metrics
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    median_ae = median_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
    
    # Accuracy within thresholds
    errors = np.abs(y_test - predictions) / y_test
    acc_10 = (errors <= 0.10).mean() * 100
    acc_20 = (errors <= 0.20).mean() * 100
    acc_25 = (errors <= 0.25).mean() * 100
    
    print(f"\n{'='*80}")
    print(f"🏆 {category.upper()} MODEL PERFORMANCE")
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
    
    # Save models
    ensemble = {
        'xgb': xgb_model,
        'lgb': lgb_model,
        'rf': rf_model,
        'gb': gb_model,
        'weights': weights
    }
    
    model_dir = Path('trained_models')
    model_dir.mkdir(exist_ok=True)
    
    joblib.dump(ensemble, model_dir / f'{category}_model.pkl')
    joblib.dump(scaler, model_dir / f'{category}_scaler.pkl')
    
    # Save metadata
    metadata = {
        'category': category,
        'training_date': datetime.now().isoformat(),
        'samples': len(df_clean),
        'features': X.shape[1],
        'feature_names': list(X.columns),
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
    
    with open(model_dir / f'model_metadata_{category}.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved models to trained_models/\n")
    
    return {
        'r2': r2,
        'mae': mae,
        'acc_20': acc_20
    }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🚀 EZSELL ML PIPELINE - FIXED DATA TRAINING")
    print("="*80 + "\n")
    
    base_path = Path(r"C:\Users\ahmed\Downloads\ezsell\ezsell")
    results = {}
    
    # ========== MOBILE ==========
    print("\n" + "="*80)
    print("📱 MOBILE CATEGORY")
    print("="*80)
    
    mobile_df = pd.read_csv(base_path / "cleaned_mobiles.csv")
    print(f"📥 Loaded {len(mobile_df):,} mobile rows")
    
    # Extract features
    mobile_features = []
    for idx, row in mobile_df.iterrows():
        try:
            feats = extract_mobile_features(row)
            feats['price'] = row['Price']
            mobile_features.append(feats)
        except:
            continue
    
    mobile_df_proc = pd.DataFrame(mobile_features)
    mobile_df_proc = mobile_df_proc[(mobile_df_proc['price'] > 1000) & (mobile_df_proc['price'] < 1000000)]
    mobile_df_proc = engineer_mobile_features(mobile_df_proc)
    
    print(f"✅ Processed {len(mobile_df_proc):,} samples")
    print(f"💰 Price range: Rs. {mobile_df_proc['price'].min():,.0f} - Rs. {mobile_df_proc['price'].max():,.0f}")
    
    # Save preprocessed
    scraped_dir = Path('scraped_data')
    scraped_dir.mkdir(exist_ok=True)
    mobile_df_proc.to_csv(scraped_dir / f'mobile_preprocessed_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
    
    results['mobile'] = train_model(mobile_df_proc, 'mobile', outlier_method='zscore')
    
    # ========== LAPTOP ==========
    print("\n" + "="*80)
    print("💻 LAPTOP CATEGORY")
    print("="*80)
    
    laptop_df = pd.read_csv(base_path / "laptops.csv", on_bad_lines='skip')
    print(f"📥 Loaded {len(laptop_df):,} laptop rows")
    
    # FIX PRICES - multiply by 1000 if < 1000
    laptop_df['Price'] = pd.to_numeric(laptop_df['Price'], errors='coerce')
    laptop_df.loc[laptop_df['Price'] < 1000, 'Price'] = laptop_df.loc[laptop_df['Price'] < 1000, 'Price'] * 1000
    print(f"💰 Fixed prices: Rs. {laptop_df['Price'].min():,.0f} - Rs. {laptop_df['Price'].max():,.0f}")
    
    # Extract features
    laptop_features = []
    for idx, row in laptop_df.iterrows():
        try:
            feats = extract_laptop_features(row)
            feats['price'] = row['Price']
            laptop_features.append(feats)
        except:
            continue
    
    laptop_df_proc = pd.DataFrame(laptop_features)
    laptop_df_proc = laptop_df_proc[(laptop_df_proc['price'] > 5000) & (laptop_df_proc['price'] < 1500000)]
    laptop_df_proc = engineer_laptop_features(laptop_df_proc)
    
    print(f"✅ Processed {len(laptop_df_proc):,} samples")
    
    laptop_df_proc.to_csv(scraped_dir / f'laptop_preprocessed_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
    
    results['laptop'] = train_model(laptop_df_proc, 'laptop', outlier_method='iqr')
    
    # ========== FURNITURE ==========
    print("\n" + "="*80)
    print("🪑 FURNITURE CATEGORY")
    print("="*80)
    
    furniture_df = pd.read_csv(base_path / "furniture.csv", on_bad_lines='skip')
    print(f"📥 Loaded {len(furniture_df):,} furniture rows")
    
    # FIX PRICES - multiply by 1000 if < 1000
    furniture_df['Price'] = pd.to_numeric(furniture_df['Price'], errors='coerce')
    furniture_df.loc[furniture_df['Price'] < 1000, 'Price'] = furniture_df.loc[furniture_df['Price'] < 1000, 'Price'] * 1000
    print(f"💰 Fixed prices: Rs. {furniture_df['Price'].min():,.0f} - Rs. {furniture_df['Price'].max():,.0f}")
    
    # Extract features
    furniture_features = []
    for idx, row in furniture_df.iterrows():
        try:
            feats = extract_furniture_features(row)
            feats['price'] = row['Price']
            furniture_features.append(feats)
        except:
            continue
    
    furniture_df_proc = pd.DataFrame(furniture_features)
    furniture_df_proc = furniture_df_proc[(furniture_df_proc['price'] > 1000) & (furniture_df_proc['price'] < 1000000)]
    furniture_df_proc = engineer_furniture_features(furniture_df_proc)
    
    print(f"✅ Processed {len(furniture_df_proc):,} samples")
    
    furniture_df_proc.to_csv(scraped_dir / f'furniture_preprocessed_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
    
    results['furniture'] = train_model(furniture_df_proc, 'furniture', outlier_method='iqr')
    
    # ========== SUMMARY ==========
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE - FINAL RESULTS")
    print("="*80)
    for cat, metrics in results.items():
        status = "✅" if metrics['r2'] >= 0.80 else "⚠️"
        print(f"{status} {cat.upper():12} : R²={metrics['r2']*100:5.2f}% | MAE=Rs. {metrics['mae']:7,.0f} | ±20%={metrics['acc_20']:5.2f}%")
    print("="*80)
    print("\n✅ All models saved to trained_models/")
    print("✅ Preprocessed data saved to scraped_data/")
    print("\n🚀 Ready for production use!\n")

if __name__ == "__main__":
    main()
