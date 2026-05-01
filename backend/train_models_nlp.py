"""
🚀 NLP-Based Model Training Pipeline
Production-ready training with advanced NLP feature extraction
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

from nlp_feature_extractor import NLPFeatureExtractor

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def preprocess_data_with_nlp(df: pd.DataFrame, category: str, extractor: NLPFeatureExtractor) -> pd.DataFrame:
    """
    Preprocess data using NLP feature extraction
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🧠 NLP-Based Feature Extraction for {category.upper()}")
    logger.info(f"{'='*80}")
    
    # Initialize features list
    features_list = []
    
    # Extract features for each row
    for idx, row in df.iterrows():
        title = str(row.get('title', ''))
        description = str(row.get('description', ''))
        
        if category == 'mobile':
            features = extractor.extract_mobile_features(title, description)
        elif category == 'laptop':
            features = extractor.extract_laptop_features(title, description)
        elif category == 'furniture':
            features = extractor.extract_furniture_features(title, description)
        else:
            features = {}
        
        # Add engineered features
        features = extractor.create_engineered_features(features, category)
        
        # Keep price
        features['price'] = row.get('price', 0)
        
        features_list.append(features)
    
    # Create new dataframe with extracted features
    processed_df = pd.DataFrame(features_list)
    
    logger.info(f"✅ Extracted {len(processed_df.columns)} features from {len(processed_df)} samples")
    logger.info(f"📊 Features: {list(processed_df.columns)}")
    
    return processed_df


def train_model_with_nlp(csv_file: str, category: str):
    """Train production model with NLP-based feature extraction"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔥 TRAINING {category.upper()} MODEL WITH NLP")
    logger.info(f"📁 Data: {csv_file}")
    logger.info('='*80)
    
    # Load raw data
    df = pd.read_csv(csv_file)
    logger.info(f"📊 Loaded {len(df)} raw samples")
    
    # Initialize NLP extractor
    extractor = NLPFeatureExtractor()
    
    # Extract features using NLP
    df = preprocess_data_with_nlp(df, category, extractor)
    
    # CRITICAL: Remove rows with NaN or invalid prices
    initial_len = len(df)
    df = df.dropna(subset=['price'])  # Drop rows with NaN price
    df = df[df['price'] > 0]  # Remove invalid prices
    df = df[df['price'] < 10000000]  # Remove unrealistic prices (>10M PKR)
    df = df[~np.isinf(df['price'])]  # Remove infinity values
    logger.info(f"🧹 Removed {initial_len - len(df)} rows with invalid prices")
    
    if len(df) < 50:
        logger.error(f"❌ Only {len(df)} valid samples remaining, cannot train model")
        return None
    
    # Clean outliers using IQR method
    Q1 = df['price'].quantile(0.05)
    Q3 = df['price'].quantile(0.95)
    IQR = Q3 - Q1
    lower_bound = Q1 - 2.5 * IQR
    upper_bound = Q3 + 2.5 * IQR
    
    before_outlier = len(df)
    df = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
    logger.info(f"🧹 Removed {before_outlier - len(df)} outliers (IQR method)")
    logger.info(f"✅ Clean dataset: {len(df)} samples")
    
    # Update price_category based on actual prices
    df['price_percentile'] = df['price'].rank(pct=True)
    try:
        df['price_bin'] = pd.qcut(df['price'], q=5, labels=False, duplicates='drop') + 1
    except:
        df['price_bin'] = (df['price_percentile'] * 5).astype(int) + 1
        df['price_bin'] = df['price_bin'].clip(1, 5)
    
    # Update price_category in features
    if 'price_category' in df.columns:
        df['price_category'] = df['price_bin']
    
    # Replace any remaining NaN/Inf values with 0
    df = df.replace([np.inf, -np.inf], 0)
    df = df.fillna(0)
    
    # Separate features and target
    X = df.drop(['price', 'price_percentile', 'price_bin'], axis=1, errors='ignore')
    y = df['price'].copy()
    
    logger.info(f"\n📊 Feature Summary:")
    logger.info(f"   Total features: {len(X.columns)}")
    logger.info(f"   Features: {list(X.columns)}")
    logger.info(f"   Target range: Rs. {y.min():,.0f} to Rs. {y.max():,.0f}")
    logger.info(f"   Target mean: Rs. {y.mean():,.0f}")
    
    # Train-test split (stratified by price bins)
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=df['price_bin'], random_state=42
        )
    except:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    logger.info(f"\n📊 Data Split:")
    logger.info(f"   Training: {len(X_train)} samples")
    logger.info(f"   Testing: {len(X_test)} samples")
    
    # Scale features
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train ensemble models
    logger.info(f"\n🤖 Training Ensemble Models...")
    
    models = {}
    
    # XGBoost
    logger.info("   Training XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=12,
        min_child_weight=1,
        subsample=0.85,
        colsample_bytree=0.85,
        gamma=0.01,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train_scaled, y_train, verbose=False)
    models['xgboost'] = xgb_model
    
    # LightGBM
    logger.info("   Training LightGBM...")
    lgb_model = lgb.LGBMRegressor(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=15,
        num_leaves=60,
        min_child_samples=15,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(X_train_scaled, y_train)
    models['lightgbm'] = lgb_model
    
    # Random Forest
    logger.info("   Training Random Forest...")
    rf_model = RandomForestRegressor(
        n_estimators=500,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    models['random_forest'] = rf_model
    
    # Gradient Boosting
    logger.info("   Training Gradient Boosting...")
    gb_model = GradientBoostingRegressor(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=10,
        min_samples_split=15,
        min_samples_leaf=5,
        subsample=0.85,
        random_state=42
    )
    gb_model.fit(X_train_scaled, y_train)
    models['gradient_boosting'] = gb_model
    
    # Create ensemble predictions
    weights = {
        'xgboost': 0.35,
        'lightgbm': 0.35,
        'random_forest': 0.15,
        'gradient_boosting': 0.15
    }
    
    # Make predictions
    ensemble_pred = np.zeros(len(X_test_scaled))
    for name, model in models.items():
        pred = model.predict(X_test_scaled)
        ensemble_pred += pred * weights[name]
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, ensemble_pred)
    rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
    r2 = r2_score(y_test, ensemble_pred)
    
    # Calculate accuracy within ranges
    errors = np.abs(ensemble_pred - y_test.values)
    pct_errors = errors / y_test.values * 100
    
    acc_10 = np.mean(pct_errors <= 10) * 100
    acc_20 = np.mean(pct_errors <= 20) * 100
    acc_25 = np.mean(pct_errors <= 25) * 100
    
    # Print results
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 MODEL PERFORMANCE - {category.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"R² Score:            {r2*100:.2f}%")
    logger.info(f"MAE:                 Rs. {mae:,.0f}")
    logger.info(f"RMSE:                Rs. {rmse:,.0f}")
    logger.info(f"Median Abs Error:    Rs. {np.median(errors):,.0f}")
    logger.info(f"")
    logger.info(f"Accuracy ±10%:       {acc_10:.2f}%")
    logger.info(f"Accuracy ±20%:       {acc_20:.2f}%")
    logger.info(f"Accuracy ±25%:       {acc_25:.2f}%")
    logger.info(f"{'='*80}")
    
    # Save models
    save_dir = Path('trained_models')
    save_dir.mkdir(exist_ok=True)
    
    # Create ensemble model dict
    ensemble_model = {
        'models': models,
        'weights': weights,
        'scaler': scaler,
        'feature_names': list(X.columns)
    }
    
    model_path = save_dir / f'{category}_model.pkl'
    joblib.dump(ensemble_model, model_path)
    logger.info(f"💾 Saved model: {model_path}")
    
    # Save scaler separately (for compatibility)
    scaler_path = save_dir / f'{category}_scaler.pkl'
    joblib.dump(scaler, scaler_path)
    logger.info(f"💾 Saved scaler: {scaler_path}")
    
    # Save metadata
    metadata = {
        'category': category,
        'training_date': datetime.now().isoformat(),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'features': list(X.columns),
        'feature_count': len(X.columns),
        'metrics': {
            'r2_score': float(r2),
            'mae': float(mae),
            'rmse': float(rmse),
            'median_ae': float(np.median(errors)),
            'accuracy_10pct': float(acc_10),
            'accuracy_20pct': float(acc_20),
            'accuracy_25pct': float(acc_25)
        },
        'ensemble_weights': weights,
        'price_range': {
            'min': float(y.min()),
            'max': float(y.max()),
            'mean': float(y.mean()),
            'median': float(y.median())
        }
    }
    
    metadata_path = save_dir / f'model_metadata_{category}.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"💾 Saved metadata: {metadata_path}")
    
    return ensemble_model, metadata


def main():
    """Train all models with NLP preprocessing"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 NLP-BASED MODEL TRAINING PIPELINE")
    logger.info(f"{'='*80}\n")
    
    categories = {
        'mobile': 'scraped_data/mobile_preprocessed_20251213_new.csv',
        'laptop': 'scraped_data/laptop_preprocessed_20251213_new.csv',
        'furniture': 'scraped_data/furniture_preprocessed_20251213_new.csv'
    }
    
    results = {}
    
    for category, csv_file in categories.items():
        csv_path = Path(csv_file)
        
        if not csv_path.exists():
            logger.warning(f"⚠️  Skipping {category}: {csv_file} not found")
            continue
        
        try:
            model, metadata = train_model_with_nlp(csv_file, category)
            results[category] = {
                'success': True,
                'r2_score': metadata['metrics']['r2_score'],
                'accuracy_20pct': metadata['metrics']['accuracy_20pct']
            }
        except Exception as e:
            logger.error(f"❌ Failed to train {category}: {e}")
            results[category] = {'success': False, 'error': str(e)}
        
        logger.info("\n")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 TRAINING SUMMARY")
    logger.info(f"{'='*80}")
    
    for category, result in results.items():
        if result.get('success'):
            logger.info(f"✅ {category.upper():12} - R²: {result['r2_score']*100:5.2f}% | ±20% Acc: {result['accuracy_20pct']:5.2f}%")
        else:
            logger.info(f"❌ {category.upper():12} - FAILED: {result.get('error', 'Unknown error')}")
    
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()
