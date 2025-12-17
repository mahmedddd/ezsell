"""
🚀 Train Production Models - Quick Retrain Script
"""

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
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def train_model(csv_file: str, category: str):
    """Train production model for a category"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔥 TRAINING {category.upper()} MODEL")
    logger.info(f"📁 Data: {csv_file}")
    logger.info('='*80)
    
    # Load data
    df = pd.read_csv(csv_file)
    logger.info(f"📊 Loaded {len(df)} samples")
    
    # Clean outliers
    z_scores = np.abs(stats.zscore(df['price']))
    df = df[z_scores < 3.0]  # Less strict than 2.5
    
    if len(df) < 100:
        logger.warning(f"⚠️ Only {len(df)} samples after outlier removal, skipping Z-score filter")
        df = pd.read_csv(csv_file)  # Reload without outlier removal
    
    logger.info(f"✅ After outlier removal: {len(df)} samples")
    
    # Price features
    df['price_percentile'] = df['price'].rank(pct=True)
    
    # Try to create price bins, handle duplicates
    try:
        df['price_bin'] = pd.qcut(df['price'], q=5, labels=False, duplicates='drop') + 1
    except:
        # If qcut fails, use simple percentile-based bins
        df['price_bin'] = (df['price_percentile'] * 5).astype(int) + 1
        df['price_bin'] = df['price_bin'].clip(1, 5)
    
    # Get features
    feature_cols = {
        'mobile': ['brand_premium', 'ram', 'storage', 'battery', 'camera', 'screen_size',
                   'is_5g', 'is_pta', 'is_amoled', 'has_warranty', 'has_box',
                   'condition_score', 'age_months'],
        'laptop': ['brand_premium', 'processor_tier', 'generation', 'ram', 'storage',
                   'has_gpu', 'gpu_tier', 'is_gaming', 'is_touchscreen', 'has_ssd',
                   'screen_size', 'condition_score', 'age_months'],
        'furniture': ['material_quality', 'seating_capacity', 'length', 'width', 'height', 'volume',
                     'is_imported', 'is_handmade', 'has_storage', 'is_modern', 'is_antique',
                     'condition_score']
    }
    
    available = [col for col in feature_cols[category] if col in df.columns]
    X = df[available].copy()
    y = df['price'].copy()
    
    # Add price category
    X['price_category'] = df['price_bin']
    
    # Engineer features
    if category == 'mobile':
        if 'ram' in X.columns and 'storage' in X.columns:
            X['performance'] = (X['ram'] ** 1.5) * (X['storage'] ** 0.5)
            X['ram_squared'] = X['ram'] ** 2
        if 'age_months' in X.columns:
            X['depreciation'] = np.exp(-X['age_months'] / 24)
        if 'brand_premium' in X.columns and 'ram' in X.columns:
            X['brand_ram'] = X['brand_premium'] * X['ram']
    
    elif category == 'laptop':
        if 'processor_tier' in X.columns and 'generation' in X.columns:
            X['cpu_score'] = X['processor_tier'] * X['generation']
        if 'ram' in X.columns and 'storage' in X.columns:
            X['memory_score'] = (X['ram'] ** 1.5) * (X['storage'] ** 0.5)
            X['ram_squared'] = X['ram'] ** 2
        if 'age_months' in X.columns:
            X['depreciation'] = np.exp(-X['age_months'] / 36)
        if 'gpu_tier' in X.columns:
            X['gaming_score'] = X['gpu_tier'] ** 2
    
    elif category == 'furniture':
        if 'volume' in X.columns:
            X['volume_log'] = np.log1p(X['volume'])
        if 'material_quality' in X.columns and 'condition_score' in X.columns:
            X['quality'] = X['material_quality'] * X['condition_score']
        if 'seating_capacity' in X.columns:
            X['seating_value'] = X['seating_capacity'] ** 1.5
    
    # Fill missing
    X = X.fillna(X.median())
    
    # Scale
    scaler = RobustScaler()
    feature_names = list(X.columns)
    X_scaled = scaler.fit_transform(X)
    X = pd.DataFrame(X_scaled, columns=feature_names)
    
    logger.info(f"✅ Prepared {X.shape[1]} features")
    
    # Split
    try:
        price_bins = pd.qcut(y, q=5, labels=False, duplicates='drop')
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=price_bins
        )
    except:
        # Stratification failed, do regular split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    logger.info(f"📊 Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Train ensemble
    logger.info("🤖 Training ensemble models...")
    
    # XGBoost
    logger.info("   Training XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=2000, learning_rate=0.02, max_depth=12,
        min_child_weight=1, subsample=0.85, colsample_bytree=0.85,
        gamma=0.01, reg_alpha=0.1, reg_lambda=2.0, random_state=42, n_jobs=-1
    )
    xgb_model.fit(X_train, y_train)
    
    # LightGBM
    logger.info("   Training LightGBM...")
    lgb_model = lgb.LGBMRegressor(
        n_estimators=2000, learning_rate=0.02, max_depth=15, num_leaves=60,
        min_child_samples=15, subsample=0.85, colsample_bytree=0.85,
        reg_alpha=0.1, reg_lambda=2.0, random_state=42, n_jobs=-1, verbose=-1
    )
    lgb_model.fit(X_train, y_train)
    
    # RandomForest
    logger.info("   Training RandomForest...")
    rf_model = RandomForestRegressor(
        n_estimators=500, max_depth=20, min_samples_split=10,
        min_samples_leaf=4, max_features='sqrt', random_state=42, n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    # GradientBoosting
    logger.info("   Training GradientBoost...")
    gb_model = GradientBoostingRegressor(
        n_estimators=800, learning_rate=0.03, max_depth=10,
        min_samples_split=15, min_samples_leaf=5, subsample=0.85, random_state=42
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
    logger.info("📊 Evaluating model...")
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
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔥 MODEL PERFORMANCE - {category.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"🏆 R² Score:        {r2:.4f} ({r2*100:.2f}%)")
    logger.info(f"💰 MAE:             Rs. {mae:,.2f}")
    logger.info(f"📊 Median AE:       Rs. {median_ae:,.2f}")
    logger.info(f"📈 RMSE:            Rs. {rmse:,.2f}")
    logger.info(f"📉 MAPE:            {mape:.2f}%")
    logger.info(f"✅ Accuracy (±10%): {acc_10:.2f}%")
    logger.info(f"✅ Accuracy (±20%): {acc_20:.2f}%")
    logger.info(f"✅ Accuracy (±25%): {acc_25:.2f}%")
    logger.info(f"📦 Test Samples:    {len(y_test)}")
    logger.info(f"{'='*80}\n")
    
    # Save
    models_dir = Path("trained_models")
    models_dir.mkdir(exist_ok=True)
    
    model_file = models_dir / f"{category}_model.pkl"
    scaler_file = models_dir / f"{category}_scaler.pkl"
    meta_file = models_dir / f"{category}_metadata.json"
    
    joblib.dump(ensemble, model_file)
    joblib.dump(scaler, scaler_file)
    
    metadata = {
        'category': category,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'model_type': 'Ensemble (XGB+LGB+RF+GB)',
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
    
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"💾 Saved: {model_file}")
    logger.info(f"💾 Saved: {scaler_file}")
    logger.info(f"💾 Saved: {meta_file}\n")
    
    return metadata


if __name__ == "__main__":
    logger.info("\n" + "="*80)
    logger.info("🚀 TRAINING PRODUCTION MODELS")
    logger.info("="*80)
    
    data_dir = Path("scraped_data")
    files = list(data_dir.glob("*_preprocessed_*.csv"))
    
    if not files:
        logger.error(f"❌ No preprocessed files found in {data_dir}")
        exit(1)
    
    logger.info(f"📂 Found {len(files)} files\n")
    
    results = {}
    for csv_file in files:
        category = csv_file.stem.split('_')[0]
        if category in ['mobile', 'laptop', 'furniture']:
            try:
                result = train_model(str(csv_file), category)
                results[category] = result
            except Exception as e:
                logger.error(f"❌ Error training {category}: {e}")
                import traceback
                traceback.print_exc()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("🎉 TRAINING COMPLETE")
    logger.info("="*80)
    
    for cat, res in results.items():
        status = "✅" if res['r2_score'] > 0.8 else "⚠️"
        logger.info(f"{status} {cat.upper()}: R²={res['r2_score']:.2%} | MAE=Rs.{res['mae']:,.0f} | ±20%={res['accuracy_20pct']:.1f}%")
    
    logger.info("="*80 + "\n")
