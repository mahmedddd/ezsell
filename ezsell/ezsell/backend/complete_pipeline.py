"""
🚀 Complete ML Pipeline - From Raw CSV to Production Models
Full preprocessing with NLP feature extraction + Model training
Following PRICE_PREDICTION_DOCUMENTATION.md standards
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from scipy import stats
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, median_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from brand_categorization import (
    get_brand_score, get_material_score, get_condition_score,
    get_processor_tier, get_gpu_tier, MOBILE_BRAND_SCORES,
    LAPTOP_BRAND_SCORES, MATERIAL_QUALITY_SCORES
)

print("""
╔══════════════════════════════════════════════════════════════╗
║     🚀 EZSELL ML PIPELINE - COMPLETE TRAINING SYSTEM        ║
║     From Raw Data → Preprocessed → Production Models         ║
╚══════════════════════════════════════════════════════════════╝
""")

# ============================================================================
# STEP 1: NLP FEATURE EXTRACTION FUNCTIONS
# ============================================================================

def extract_mobile_features(row):
    """Extract all features from mobile listing"""
    title = str(row.get('Title', '')).lower()
    brand = str(row.get('Brand', ''))
    condition = str(row.get('Condition', 'Used'))
    
    features = {}
    
    # Brand premium score
    features['brand_premium'] = get_brand_score(brand, 'mobile')
    
    # Extract RAM (8GB, 8/256, etc.)
    ram_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*gb', title)
    if ram_match:
        features['ram'] = int(ram_match.group(1))
    else:
        ram_match = re.search(r'(\d+)\s*gb\s*ram', title)
        if ram_match:
            features['ram'] = int(ram_match.group(1))
        else:
            features['ram'] = 4  # Default
    
    # Extract Storage
    if ram_match and '/' in title:
        storage_match = re.search(r'/\s*(\d+)\s*gb', title)
        if storage_match:
            features['storage'] = int(storage_match.group(1))
        else:
            features['storage'] = 64
    else:
        storage_match = re.search(r'(\d{2,4})\s*gb(?!\s*ram)', title)
        if storage_match:
            features['storage'] = int(storage_match.group(1))
        else:
            features['storage'] = 64
    
    # Extract camera (MP)
    camera_match = re.search(r'(\d+)\s*mp', title)
    features['camera'] = int(camera_match.group(1)) if camera_match else 0
    
    # Extract battery (mAh)
    battery_match = re.search(r'(\d{4,5})\s*mah', title)
    features['battery'] = int(battery_match.group(1)) if battery_match else 0
    
    # Extract screen size
    screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', title)
    features['screen_size'] = float(screen_match.group(1)) if screen_match else 0
    
    # Boolean features
    features['is_5g'] = 1 if '5g' in title else 0
    features['is_pta'] = 1 if 'pta' in title else 0
    features['is_amoled'] = 1 if 'amoled' in title or 'oled' in title else 0
    features['has_warranty'] = 1 if 'warranty' in title else 0
    features['has_box'] = 1 if 'box' in title or 'boxed' in title or 'pack' in title else 0
    
    # Condition score
    features['condition_score'] = get_condition_score(condition)
    
    # Age estimation (from condition)
    if 'new' in condition.lower() or 'brand new' in title:
        features['age_months'] = 0
    elif 'excellent' in condition.lower() or 'mint' in title:
        features['age_months'] = 3
    elif 'good' in condition.lower():
        features['age_months'] = 12
    elif 'used' in condition.lower():
        features['age_months'] = 18
    else:
        features['age_months'] = 12
    
    return features


def extract_laptop_features(row):
    """Extract all features from laptop listing"""
    title = str(row.get('Title', '')).lower()
    description = str(row.get('Description', '')).lower()
    brand = str(row.get('Brand', ''))
    condition = str(row.get('Condition', 'Used'))
    combined = title + ' ' + description
    
    features = {}
    
    # Brand premium
    features['brand_premium'] = get_brand_score(brand, 'laptop')
    
    # Processor tier
    proc_match = re.search(r'(i[3579]|ryzen\s*[3579]|m[123]|celeron|pentium)', combined)
    if proc_match:
        features['processor_tier'] = get_processor_tier(proc_match.group(1))
    else:
        features['processor_tier'] = 5
    
    # Generation
    gen_match = re.search(r'(\d+)(?:th)?\s*gen', combined)
    if gen_match:
        features['generation'] = int(gen_match.group(1))
    else:
        features['generation'] = 10
    
    # RAM
    ram_match = re.search(r'(\d+)\s*gb\s*ram', combined)
    if ram_match:
        features['ram'] = int(ram_match.group(1))
    else:
        features['ram'] = 8
    
    # Storage
    storage_match = re.search(r'(\d+)\s*(?:gb|tb)\s*(?:ssd|hdd|storage)', combined)
    if storage_match:
        storage = int(storage_match.group(1))
        if 'tb' in storage_match.group(0):
            storage *= 1024
        features['storage'] = storage
    else:
        features['storage'] = 256
    
    # GPU detection
    gpu_match = re.search(r'(rtx|gtx|mx|radeon|vega|intel\s*(?:uhd|hd)|nvidia)', combined)
    if gpu_match:
        features['has_gpu'] = 1
        gpu_text = gpu_match.group(0)
        features['gpu_tier'] = get_gpu_tier(gpu_text)
    else:
        features['has_gpu'] = 0
        features['gpu_tier'] = 0
    
    # Boolean features
    features['is_gaming'] = 1 if 'gaming' in combined or 'predator' in combined or 'rog' in combined else 0
    features['is_touchscreen'] = 1 if 'touch' in combined or 'touchscreen' in combined else 0
    features['has_ssd'] = 1 if 'ssd' in combined else 0
    
    # Screen size
    screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', combined)
    features['screen_size'] = float(screen_match.group(1)) if screen_match else 15.6
    
    # Condition score
    features['condition_score'] = get_condition_score(condition)
    
    # Age estimation
    if 'new' in condition.lower() or 'brand new' in title:
        features['age_months'] = 0
    elif 'excellent' in condition.lower():
        features['age_months'] = 6
    elif 'good' in condition.lower():
        features['age_months'] = 12
    else:
        features['age_months'] = 24
    
    return features


def extract_furniture_features(row):
    """Extract all features from furniture listing"""
    title = str(row.get('Title', '')).lower()
    description = str(row.get('Description', '')).lower()
    material = str(row.get('Material', ''))
    condition = str(row.get('Condition', 'Used'))
    furniture_type = str(row.get('Type', '')).lower()
    combined = title + ' ' + description
    
    features = {}
    
    # Material quality
    if material and material != 'nan':
        features['material_quality'] = get_material_score(material)
    else:
        # Extract from title/description
        for mat_name in MATERIAL_QUALITY_SCORES.keys():
            if mat_name.lower() in combined:
                features['material_quality'] = get_material_score(mat_name)
                break
        else:
            features['material_quality'] = 5
    
    # Seating capacity
    seating_match = re.search(r'(\d+)\s*seater', combined)
    if seating_match:
        features['seating_capacity'] = int(seating_match.group(1))
    else:
        if 'sofa' in furniture_type:
            features['seating_capacity'] = 3
        elif 'chair' in furniture_type:
            features['seating_capacity'] = 1
        else:
            features['seating_capacity'] = 0
    
    # Dimensions (in cm)
    # Try format: 200×100×95 or 200x100x95 or 200 x 100 x 95
    dim_match = re.search(r'(\d{2,3})\s*[x×]\s*(\d{2,3})\s*[x×]\s*(\d{2,3})', combined)
    if dim_match:
        features['length'] = int(dim_match.group(1))
        features['width'] = int(dim_match.group(2))
        features['height'] = int(dim_match.group(3))
    else:
        # Default sizes based on type
        if 'sofa' in furniture_type or 'sofa' in combined:
            features['length'] = 180
            features['width'] = 90
            features['height'] = 85
        elif 'bed' in furniture_type or 'bed' in combined:
            features['length'] = 200
            features['width'] = 150
            features['height'] = 50
        elif 'table' in furniture_type or 'table' in combined:
            features['length'] = 120
            features['width'] = 80
            features['height'] = 75
        else:
            features['length'] = 100
            features['width'] = 60
            features['height'] = 80
    
    # Volume
    features['volume'] = features['length'] * features['width'] * features['height']
    
    # Boolean features
    features['is_imported'] = 1 if 'import' in combined else 0
    features['is_handmade'] = 1 if 'handmade' in combined or 'hand made' in combined else 0
    features['has_storage'] = 1 if 'storage' in combined else 0
    features['is_modern'] = 1 if 'modern' in combined else 0
    features['is_antique'] = 1 if 'antique' in combined or 'vintage' in combined else 0
    
    # Condition score
    features['condition_score'] = get_condition_score(condition)
    
    return features


# ============================================================================
# STEP 2: FEATURE ENGINEERING
# ============================================================================

def engineer_mobile_features(df):
    """Add engineered features for mobile"""
    # Performance score
    df['performance'] = (df['ram'] ** 1.5) * (df['storage'] ** 0.5)
    df['ram_squared'] = df['ram'] ** 2
    
    # Depreciation
    df['depreciation'] = np.exp(-df['age_months'] / 24)
    
    # Brand-RAM interaction
    df['brand_ram'] = df['brand_premium'] * df['ram']
    
    # Price category estimation (1-5)
    # Based on brand premium + specs
    df['price_category'] = np.clip(
        (df['brand_premium'] / 2) + (df['ram'] / 4) + (df['storage'] / 256),
        1, 5
    ).astype(int)
    
    return df


def engineer_laptop_features(df):
    """Add engineered features for laptop"""
    # CPU score
    df['cpu_score'] = df['processor_tier'] * df['generation']
    
    # Memory score
    df['memory_score'] = (df['ram'] ** 1.5) * (df['storage'] ** 0.5)
    df['ram_squared'] = df['ram'] ** 2
    
    # Gaming score
    df['gaming_score'] = df['gpu_tier'] ** 2
    
    # Depreciation
    df['depreciation'] = np.exp(-df['age_months'] / 36)
    
    # Price category
    df['price_category'] = np.clip(
        (df['brand_premium'] / 2) + (df['processor_tier'] / 2) + (df['ram'] / 8),
        1, 5
    ).astype(int)
    
    return df


def engineer_furniture_features(df):
    """Add engineered features for furniture"""
    # Volume log
    df['volume_log'] = np.log(df['volume'] + 1)
    
    # Size tier (1=small, 2=medium, 3=large)
    df['size_tier'] = pd.cut(
        df['volume'],
        bins=[0, 500000, 1000000, np.inf],
        labels=[1, 2, 3]
    ).astype(int)
    
    # Quality score
    df['quality'] = df['material_quality'] * df['condition_score']
    
    # Seating value
    df['seating_value'] = df['seating_capacity'] ** 1.5
    
    # Price category
    df['price_category'] = np.clip(
        (df['material_quality'] / 2) + (df['seating_capacity'] / 2) + (df['size_tier']),
        1, 5
    ).astype(int)
    
    return df


# ============================================================================
# STEP 3: PREPROCESSING PIPELINE
# ============================================================================

def preprocess_category(csv_path, category, extract_func, engineer_func):
    """Complete preprocessing for a category"""
    print(f"\n{'='*80}")
    print(f"📂 PREPROCESSING {category.upper()}")
    print(f"{'='*80}")
    
    # Load raw data
    print(f"📥 Loading: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Extract features
    print(f"🔄 Extracting NLP features...")
    features_list = []
    for idx, row in df.iterrows():
        try:
            feats = extract_func(row)
            feats['price'] = row['Price']
            features_list.append(feats)
        except Exception as e:
            continue
    
    df_features = pd.DataFrame(features_list)
    print(f"✅ Extracted features from {len(df_features):,} samples")
    
    # Clean prices
    df_features = df_features[df_features['price'] > 0]
    df_features = df_features[df_features['price'] < 10000000]  # Remove outliers
    print(f"✅ After price filter: {len(df_features):,} samples")
    
    # Engineer features
    print(f"🔧 Engineering features...")
    df_features = engineer_func(df_features)
    print(f"✅ Total features: {len(df_features.columns)}")
    
    # Save preprocessed data
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{category}_preprocessed_{datetime.now().strftime('%Y%m%d')}.csv"
    df_features.to_csv(output_path, index=False)
    print(f"💾 Saved: {output_path}")
    
    print(f"\n📊 Feature Summary:")
    print(f"   Samples: {len(df_features):,}")
    print(f"   Features: {len(df_features.columns) - 1}")  # Exclude price
    print(f"   Price Range: Rs. {df_features['price'].min():,.0f} - Rs. {df_features['price'].max():,.0f}")
    print(f"   Price Mean: Rs. {df_features['price'].mean():,.0f}")
    
    return df_features


# ============================================================================
# STEP 4: MODEL TRAINING
# ============================================================================

def train_ensemble(X_train, y_train, category):
    """Train ensemble with documentation hyperparameters"""
    print("\n🤖 Training ensemble models...")
    
    # Mobile gets more estimators
    n_est = 2500 if category == 'mobile' else 2000
    max_d = 14 if category == 'mobile' else 12
    
    models = {}
    
    # XGBoost
    print("   ⚡ XGBoost...")
    models['xgb'] = XGBRegressor(
        n_estimators=n_est,
        learning_rate=0.02,
        max_depth=max_d,
        min_child_weight=1,
        subsample=0.85,
        colsample_bytree=0.85,
        gamma=0.01,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        verbosity=0
    )
    models['xgb'].fit(X_train, y_train)
    
    # LightGBM
    print("   💡 LightGBM...")
    models['lgb'] = LGBMRegressor(
        n_estimators=n_est,
        learning_rate=0.02,
        max_depth=15,
        num_leaves=60,
        min_child_samples=15,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        verbose=-1
    )
    models['lgb'].fit(X_train, y_train)
    
    # Random Forest
    print("   🌲 RandomForest...")
    models['rf'] = RandomForestRegressor(
        n_estimators=500,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    models['rf'].fit(X_train, y_train)
    
    # Gradient Boosting
    print("   📈 GradientBoost...")
    models['gb'] = GradientBoostingRegressor(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=10,
        min_samples_split=15,
        min_samples_leaf=5,
        subsample=0.85,
        random_state=42
    )
    models['gb'].fit(X_train, y_train)
    
    # Ensemble dict
    ensemble = {
        'xgb': models['xgb'],
        'lgb': models['lgb'],
        'rf': models['rf'],
        'gb': models['gb'],
        'weights': [0.35, 0.35, 0.15, 0.15]
    }
    
    return ensemble


def evaluate_model(ensemble, scaler, X_test, y_test):
    """Evaluate ensemble model"""
    X_test_scaled = scaler.transform(X_test)
    
    # Weighted prediction
    predictions = np.zeros(len(X_test))
    for model_name, weight in zip(['xgb', 'lgb', 'rf', 'gb'], ensemble['weights']):
        predictions += ensemble[model_name].predict(X_test_scaled) * weight
    
    # Metrics
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    median_ae = median_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
    
    errors = np.abs(y_test - predictions)
    acc_10 = np.mean(errors <= y_test * 0.10) * 100
    acc_20 = np.mean(errors <= y_test * 0.20) * 100
    acc_25 = np.mean(errors <= y_test * 0.25) * 100
    
    return {
        'r2_score': r2,
        'mae': mae,
        'median_ae': median_ae,
        'rmse': rmse,
        'mape': mape,
        'accuracy_10': acc_10,
        'accuracy_20': acc_20,
        'accuracy_25': acc_25
    }


def train_category_model(df, category, outlier_method='zscore'):
    """Train model for a category"""
    print(f"\n{'='*80}")
    print(f"🔥 TRAINING {category.upper()} MODEL")
    print(f"{'='*80}")
    
    # Remove outliers
    if outlier_method == 'zscore':
        z_scores = np.abs(stats.zscore(df['price']))
        df_clean = df[z_scores < 3.0].copy()
        print(f"🧹 Z-score outlier removal: {len(df) - len(df_clean)} removed, {len(df_clean):,} retained")
    else:
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        df_clean = df[(df['price'] >= Q1 - 2.5*IQR) & (df['price'] <= Q3 + 2.5*IQR)].copy()
        print(f"🧹 IQR outlier removal: {len(df) - len(df_clean)} removed, {len(df_clean):,} retained")
    
    # Separate features and target
    X = df_clean.drop('price', axis=1)
    y = df_clean['price']
    
    print(f"✅ Training data: {len(X):,} samples, {len(X.columns)} features")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"📊 Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    # Scale
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train
    ensemble = train_ensemble(X_train_scaled, y_train, category)
    
    # Evaluate
    print("\n📊 Evaluating...")
    metrics = evaluate_model(ensemble, scaler, X_test, y_test)
    
    # Print results
    print(f"\n{'='*80}")
    print(f"🏆 {category.upper()} MODEL PERFORMANCE")
    print(f"{'='*80}")
    print(f"🎯 R² Score:        {metrics['r2_score']:.4f} ({metrics['r2_score']*100:.2f}%)")
    print(f"💰 MAE:             Rs. {metrics['mae']:,.2f}")
    print(f"📊 Median AE:       Rs. {metrics['median_ae']:,.2f}")
    print(f"📈 RMSE:            Rs. {metrics['rmse']:,.2f}")
    print(f"📉 MAPE:            {metrics['mape']:.2f}%")
    print(f"✅ Accuracy (±10%): {metrics['accuracy_10']:.2f}%")
    print(f"✅ Accuracy (±20%): {metrics['accuracy_20']:.2f}%")
    print(f"✅ Accuracy (±25%): {metrics['accuracy_25']:.2f}%")
    print(f"📦 Test Samples:    {len(X_test):,}")
    print(f"{'='*80}\n")
    
    # Save models
    models_dir = Path("trained_models")
    models_dir.mkdir(exist_ok=True)
    
    joblib.dump(ensemble, models_dir / f"{category}_model.pkl")
    joblib.dump(scaler, models_dir / f"{category}_scaler.pkl")
    
    metadata = {
        'category': category,
        'training_date': datetime.now().isoformat(),
        'samples': len(X),
        'features': len(X.columns),
        'feature_names': list(X.columns),
        'metrics': metrics
    }
    
    with open(models_dir / f"model_metadata_{category}.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved models to trained_models/")
    
    return metrics


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    # Paths to raw CSV files
    base_path = Path(__file__).parent.parent.parent
    mobile_csv = base_path / "cleaned_mobiles.csv"
    laptop_csv = base_path / "laptops.csv"
    furniture_csv = base_path / "furniture.csv"
    
    print(f"\n📂 Looking for data files in: {base_path}")
    print(f"   Mobile: {mobile_csv.exists()}")
    print(f"   Laptop: {laptop_csv.exists()}")
    print(f"   Furniture: {furniture_csv.exists()}")
    
    results = {}
    
    # ==================== MOBILE ====================
    if mobile_csv.exists():
        print("\n" + "="*80)
        print("📱 MOBILE PIPELINE")
        print("="*80)
        df_mobile = preprocess_category(
            mobile_csv, 'mobile',
            extract_mobile_features,
            engineer_mobile_features
        )
        results['mobile'] = train_category_model(df_mobile, 'mobile', outlier_method='zscore')
    
    # ==================== LAPTOP ====================
    if laptop_csv.exists():
        print("\n" + "="*80)
        print("💻 LAPTOP PIPELINE")
        print("="*80)
        df_laptop = preprocess_category(
            laptop_csv, 'laptop',
            extract_laptop_features,
            engineer_laptop_features
        )
        results['laptop'] = train_category_model(df_laptop, 'laptop', outlier_method='iqr')
    
    # ==================== FURNITURE ====================
    if furniture_csv.exists():
        print("\n" + "="*80)
        print("🪑 FURNITURE PIPELINE")
        print("="*80)
        df_furniture = preprocess_category(
            furniture_csv, 'furniture',
            extract_furniture_features,
            engineer_furniture_features
        )
        results['furniture'] = train_category_model(df_furniture, 'furniture', outlier_method='iqr')
    
    # ==================== SUMMARY ====================
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE - FINAL SUMMARY")
    print("="*80)
    for cat, metrics in results.items():
        status = "✅" if metrics['r2_score'] > 0.70 else "⚠️" if metrics['r2_score'] > 0.50 else "❌"
        print(f"{status} {cat.upper():10s}: R²={metrics['r2_score']*100:6.2f}% | MAE=Rs.{metrics['mae']:8,.0f} | ±20%={metrics['accuracy_20']:5.1f}%")
    print("="*80)
    print("\n✅ All models saved to trained_models/")
    print("✅ Preprocessed data saved to scraped_data/")
    print("\n🚀 Ready for production use!")


if __name__ == "__main__":
    main()
