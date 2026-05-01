"""
🚀 Optimized NLP-Based Model Training Pipeline
Improved preprocessing and hyperparameters based on PRICE_PREDICTION_DOCUMENTATION.md
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


def advanced_outlier_removal(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    Apply category-specific outlier removal strategies
    Mobile: Z-score (works better for mobile as per documentation)
    Laptop/Furniture: IQR (more robust for skewed distributions)
    """
    initial_len = len(df)
    
    if category == 'mobile':
        # Z-score method for mobile (as per optimize_mobile.py success)
        z_scores = np.abs(stats.zscore(df['price']))
        df = df[z_scores < 3.0]
        logger.info(f"🧹 Removed {initial_len - len(df)} outliers (Z-score method)")
    else:
        # IQR method for laptop/furniture
        Q1 = df['price'].quantile(0.05)
        Q3 = df['price'].quantile(0.95)
        IQR = Q3 - Q1
        lower_bound = Q1 - 2.5 * IQR
        upper_bound = Q3 + 2.5 * IQR
        
        df = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
        logger.info(f"🧹 Removed {initial_len - len(df)} outliers (IQR method)")
    
    return df


def preprocess_data_with_nlp(df: pd.DataFrame, category: str, extractor: NLPFeatureExtractor) -> pd.DataFrame:
    """
    Use pre-extracted features from CSV and add engineered features
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🧠 Using Pre-Extracted Features for {category.upper()}")
    logger.info(f"{'='*80}")
    
    # The CSV already has features extracted, we just need to add engineered features
    # Keep only relevant columns based on category
    feature_cols_map = {
        'mobile': ['brand_premium', 'ram', 'storage', 'battery', 'camera', 'screen_size',
                   'is_5g', 'is_pta', 'is_amoled', 'has_warranty', 'has_box',
                   'condition_score', 'age_months', 'price'],
        'laptop': ['brand_premium', 'processor_tier', 'generation', 'ram', 'storage',
                   'has_gpu', 'gpu_tier', 'is_gaming', 'is_touchscreen', 'has_ssd',
                   'screen_size', 'condition_score', 'age_months', 'price'],
        'furniture': ['material_quality', 'seating_capacity', 'length', 'width', 'height',
                     'volume', 'is_imported', 'is_handmade', 'has_storage', 'is_modern',
                     'is_antique', 'condition_score', 'price']
    }
    
    # Keep available columns
    available_cols = [col for col in feature_cols_map[category] if col in df.columns]
    processed_df = df[available_cols].copy()
    
    # Add engineered features
    if category == 'mobile':
        if 'ram' in processed_df.columns and 'storage' in processed_df.columns:
            processed_df['performance'] = (processed_df['ram'] ** 1.5) * (processed_df['storage'] ** 0.5)
            processed_df['ram_squared'] = processed_df['ram'] ** 2
        if 'age_months' in processed_df.columns:
            processed_df['depreciation'] = np.exp(-processed_df['age_months'] / 24)
        if 'brand_premium' in processed_df.columns and 'ram' in processed_df.columns:
            processed_df['brand_ram'] = processed_df['brand_premium'] * processed_df['ram']
    
    elif category == 'laptop':
        if 'processor_tier' in processed_df.columns and 'generation' in processed_df.columns:
            processed_df['cpu_score'] = processed_df['processor_tier'] * processed_df['generation']
        if 'ram' in processed_df.columns and 'storage' in processed_df.columns:
            processed_df['memory_score'] = (processed_df['ram'] ** 1.5) * (processed_df['storage'] ** 0.5)
            processed_df['ram_squared'] = processed_df['ram'] ** 2
        if 'gpu_tier' in processed_df.columns:
            processed_df['gaming_score'] = processed_df['gpu_tier'] ** 2
        if 'age_months' in processed_df.columns:
            processed_df['depreciation'] = np.exp(-processed_df['age_months'] / 36)
    
    elif category == 'furniture':
        if 'volume' in processed_df.columns:
            processed_df['volume'] = processed_df['volume'].fillna(0)
            processed_df['volume_log'] = np.log(processed_df['volume'] + 1)
            processed_df['size_tier'] = pd.cut(processed_df['volume'], 
                                               bins=[-1, 500000, 1000000, np.inf], 
                                               labels=[1, 2, 3]).astype(float)
        if 'material_quality' in processed_df.columns and 'condition_score' in processed_df.columns:
            processed_df['quality'] = processed_df['material_quality'] * processed_df['condition_score']
        if 'seating_capacity' in processed_df.columns:
            processed_df['seating_value'] = processed_df['seating_capacity'] ** 1.5
    
    logger.info(f"✅ Using {len(processed_df.columns)} features from {len(processed_df)} samples")
    logger.info(f"📊 Features: {list(processed_df.columns)}")
    
    return processed_df


def get_optimized_hyperparameters(category: str, n_samples: int):
    """
    Get category-specific optimized hyperparameters
    Based on PRICE_PREDICTION_DOCUMENTATION.md best practices
    """
    # Adjust n_estimators based on dataset size
    base_estimators = min(2000, max(1000, n_samples // 3))
    
    params = {
        'xgboost': {
            'n_estimators': base_estimators,
            'learning_rate': 0.02,
            'max_depth': 12,
            'min_child_weight': 1,
            'subsample': 0.85,
            'colsample_bytree': 0.85,
            'gamma': 0.01,
            'reg_alpha': 0.1,
            'reg_lambda': 2.0,
            'random_state': 42,
            'n_jobs': -1
        },
        'lightgbm': {
            'n_estimators': base_estimators,
            'learning_rate': 0.02,
            'max_depth': 15,
            'num_leaves': 60,
            'min_child_samples': 15,
            'subsample': 0.85,
            'colsample_bytree': 0.85,
            'reg_alpha': 0.1,
            'reg_lambda': 2.0,
            'random_state': 42,
            'n_jobs': -1,
            'verbose': -1
        },
        'random_forest': {
            'n_estimators': min(500, n_samples // 2),
            'max_depth': 20,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1
        },
        'gradient_boosting': {
            'n_estimators': min(800, n_samples // 2),
            'learning_rate': 0.03,
            'max_depth': 10,
            'min_samples_split': 15,
            'min_samples_leaf': 5,
            'subsample': 0.85,
            'random_state': 42
        }
    }
    
    # Category-specific adjustments
    if category == 'mobile':
        # Mobile needs more trees for better generalization
        params['xgboost']['n_estimators'] = min(2500, base_estimators + 500)
        params['lightgbm']['n_estimators'] = min(2500, base_estimators + 500)
        params['xgboost']['max_depth'] = 14  # Deeper for complex patterns
        
    elif category == 'laptop':
        # Laptop already performs well, minor tuning
        params['lightgbm']['num_leaves'] = 80
        params['random_forest']['max_depth'] = 25
        
    elif category == 'furniture':
        # Furniture needs more regularization
        params['xgboost']['reg_lambda'] = 3.0
        params['lightgbm']['reg_lambda'] = 3.0
        params['xgboost']['max_depth'] = 15
    
    return params


def train_model_optimized(csv_file: str, category: str):
    """Train optimized model with enhanced preprocessing"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔥 TRAINING OPTIMIZED {category.upper()} MODEL")
    logger.info(f"📁 Data: {csv_file}")
    logger.info('='*80)
    
    # Load raw data
    df = pd.read_csv(csv_file)
    logger.info(f"📊 Loaded {len(df)} raw samples")
    
    # Initialize NLP extractor
    extractor = NLPFeatureExtractor()
    
    # Extract features using NLP
    df = preprocess_data_with_nlp(df, category, extractor)
    
    # CRITICAL: Remove invalid prices
    initial_len = len(df)
    df = df.dropna(subset=['price'])
    df = df[df['price'] > 0]
    df = df[df['price'] < 10000000]
    df = df[~np.isinf(df['price'])]
    logger.info(f"🧹 Removed {initial_len - len(df)} rows with invalid prices")
    
    if len(df) < 100:
        logger.error(f"❌ Only {len(df)} valid samples remaining, cannot train model")
        return None
    
    # Apply category-specific outlier removal
    df = advanced_outlier_removal(df, category)
    logger.info(f"✅ Clean dataset: {len(df)} samples")
    
    # Create price bins for stratification only (DO NOT use as feature - data leakage!)
    df['price_percentile'] = df['price'].rank(pct=True)
    try:
        df['price_bin'] = pd.qcut(df['price'], q=5, labels=False, duplicates='drop') + 1
    except:
        df['price_bin'] = (df['price_percentile'] * 5).astype(int) + 1
        df['price_bin'] = df['price_bin'].clip(1, 5)
    
    # Replace any remaining NaN/Inf
    df = df.replace([np.inf, -np.inf], 0)
    df = df.fillna(0)
    
    # Separate features and target
    # CRITICAL: Remove price_category to prevent data leakage!
    X = df.drop(['price', 'price_percentile', 'price_bin', 'price_category'], axis=1, errors='ignore')
    y = df['price'].copy()
    
    logger.info(f"\n📊 Feature Summary:")
    logger.info(f"   Total features: {len(X.columns)}")
    logger.info(f"   Target range: Rs. {y.min():,.0f} to Rs. {y.max():,.0f}")
    logger.info(f"   Target mean: Rs. {y.mean():,.0f}")
    logger.info(f"   Target median: Rs. {y.median():,.0f}")
    
    # Stratified train-test split
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
    
    # Scale features with RobustScaler
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Get optimized hyperparameters
    params = get_optimized_hyperparameters(category, len(X_train))
    
    # Train ensemble models
    logger.info(f"\n🤖 Training Ensemble Models with Optimized Parameters...")
    
    models = {}
    
    # XGBoost
    logger.info(f"   Training XGBoost ({params['xgboost']['n_estimators']} estimators)...")
    xgb_model = xgb.XGBRegressor(**params['xgboost'])
    xgb_model.fit(X_train_scaled, y_train, verbose=False)
    models['xgboost'] = xgb_model
    
    # LightGBM
    logger.info(f"   Training LightGBM ({params['lightgbm']['n_estimators']} estimators)...")
    lgb_model = lgb.LGBMRegressor(**params['lightgbm'])
    lgb_model.fit(X_train_scaled, y_train)
    models['lightgbm'] = lgb_model
    
    # Random Forest
    logger.info(f"   Training Random Forest ({params['random_forest']['n_estimators']} estimators)...")
    rf_model = RandomForestRegressor(**params['random_forest'])
    rf_model.fit(X_train_scaled, y_train)
    models['random_forest'] = rf_model
    
    # Gradient Boosting
    logger.info(f"   Training Gradient Boosting ({params['gradient_boosting']['n_estimators']} estimators)...")
    gb_model = GradientBoostingRegressor(**params['gradient_boosting'])
    gb_model.fit(X_train_scaled, y_train)
    models['gradient_boosting'] = gb_model
    
    # Ensemble weights (as per documentation)
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
    
    # Calculate comprehensive metrics
    mae = mean_absolute_error(y_test, ensemble_pred)
    rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
    r2 = r2_score(y_test, ensemble_pred)
    
    errors = np.abs(ensemble_pred - y_test.values)
    pct_errors = errors / y_test.values * 100
    
    median_ae = np.median(errors)
    mape = np.mean(pct_errors)
    
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
    logger.info(f"Median Abs Error:    Rs. {median_ae:,.0f}")
    logger.info(f"MAPE:                {mape:.2f}%")
    logger.info(f"")
    logger.info(f"Accuracy ±10%:       {acc_10:.2f}%")
    logger.info(f"Accuracy ±20%:       {acc_20:.2f}% {'🎯 TARGET MET!' if acc_20 >= 65 else '⚠️ NEEDS IMPROVEMENT'}")
    logger.info(f"Accuracy ±25%:       {acc_25:.2f}%")
    logger.info(f"{'='*80}")
    
    # Feature importance analysis
    if hasattr(models['xgboost'], 'feature_importances_'):
        feature_importance = models['xgboost'].feature_importances_
        feature_names = X.columns
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\n🔍 Top 5 Most Important Features:")
        for idx, row in importance_df.head(5).iterrows():
            logger.info(f"   {row['feature']}: {row['importance']*100:.2f}%")
    
    # Save models
    save_dir = Path('trained_models')
    save_dir.mkdir(exist_ok=True)
    
    ensemble_model = {
        'models': models,
        'weights': weights,
        'scaler': scaler,
        'feature_names': list(X.columns)
    }
    
    model_path = save_dir / f'{category}_model.pkl'
    joblib.dump(ensemble_model, model_path)
    logger.info(f"\n💾 Saved model: {model_path}")
    
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
            'median_ae': float(median_ae),
            'mape': float(mape),
            'accuracy_10pct': float(acc_10),
            'accuracy_20pct': float(acc_20),
            'accuracy_25pct': float(acc_25)
        },
        'ensemble_weights': weights,
        'hyperparameters': params,
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
    """Train all models with optimizations"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 OPTIMIZED NLP-BASED MODEL TRAINING PIPELINE")
    logger.info(f"Based on PRICE_PREDICTION_DOCUMENTATION.md best practices")
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
            model, metadata = train_model_optimized(csv_file, category)
            results[category] = {
                'success': True,
                'r2_score': metadata['metrics']['r2_score'],
                'accuracy_20pct': metadata['metrics']['accuracy_20pct']
            }
        except Exception as e:
            logger.error(f"❌ Failed to train {category}: {e}")
            import traceback
            traceback.print_exc()
            results[category] = {'success': False, 'error': str(e)}
        
        logger.info("\n")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 TRAINING SUMMARY")
    logger.info(f"{'='*80}")
    
    targets = {
        'mobile': {'r2': 76.0, 'acc20': 67.0},
        'laptop': {'r2': 93.0, 'acc20': 84.0},
        'furniture': {'r2': 92.0, 'acc20': 66.0}
    }
    
    for category, result in results.items():
        if result.get('success'):
            r2 = result['r2_score'] * 100
            acc20 = result['accuracy_20pct']
            target_r2 = targets[category]['r2']
            target_acc20 = targets[category]['acc20']
            
            r2_status = '✅' if r2 >= target_r2 * 0.9 else '⚠️'
            acc_status = '✅' if acc20 >= target_acc20 * 0.9 else '⚠️'
            
            logger.info(f"{r2_status} {category.upper():12} - R²: {r2:5.2f}% (target: {target_r2:.0f}%) | ±20% Acc: {acc20:5.2f}% (target: {target_acc20:.0f}%) {acc_status}")
        else:
            logger.info(f"❌ {category.upper():12} - FAILED: {result.get('error', 'Unknown error')}")
    
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()
