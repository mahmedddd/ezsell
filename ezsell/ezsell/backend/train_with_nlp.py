"""
🚀 Complete Model Retraining with NLP Feature Extraction
Following PRICE_PREDICTION_DOCUMENTATION.md pipeline
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, median_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from nlp_feature_extractor import get_feature_extractor
from brand_categorization import get_brand_score, get_material_score, get_condition_score, get_processor_tier, get_gpu_tier


def load_and_extract_features(csv_path: str, category: str):
    """Load CSV and extract features using NLP"""
    print(f"\n📂 Loading: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} samples")
    
    # Clean prices
    df = df[df['price'] > 0].copy()
    print(f"✅ After price filter: {len(df)} samples")
    
    extractor = get_feature_extractor()
    features_list = []
    
    print(f"🔄 Extracting NLP features from titles...")
    for idx, row in df.iterrows():
        title = str(row.get('title', ''))
        description = str(row.get('description', ''))
        
        if category == 'mobile':
            # Extract from title using NLP
            features = extractor.extract_mobile_features(title, description)
            # Override with better brand encoding
            if 'Brand' in row and pd.notna(row['Brand']):
                features['brand_premium'] = get_brand_score(row['Brand'], 'mobile')
            if 'Condition' in row and pd.notna(row['Condition']):
                features['condition_score'] = get_condition_score(row['Condition'])
            features['price'] = row['price']
            
        elif category == 'laptop':
            features = extractor.extract_laptop_features(title, description)
            if 'Brand' in row and pd.notna(row['Brand']):
                features['brand_premium'] = get_brand_score(row['Brand'], 'laptop')
            if 'Condition' in row and pd.notna(row['Condition']):
                features['condition_score'] = get_condition_score(row['Condition'])
            features['price'] = row['price']
            
        elif category == 'furniture':
            features = extractor.extract_furniture_features(title, description)
            if 'Condition' in row and pd.notna(row['Condition']):
                features['condition_score'] = get_condition_score(row['Condition'])
            features['price'] = row['price']
        
        # Add engineered features
        features = extractor.create_engineered_features(features, category)
        features_list.append(features)
    
    # Convert to DataFrame
    df_features = pd.DataFrame(features_list)
    print(f"✅ Extracted {len(df_features.columns)} features")
    print(f"Features: {list(df_features.columns)}")
    
    return df_features


def remove_outliers(df: pd.DataFrame, method='zscore', threshold=3.0):
    """Remove price outliers"""
    from scipy import stats
    
    if method == 'zscore':
        z_scores = np.abs(stats.zscore(df['price']))
        df_clean = df[z_scores < threshold].copy()
        removed = len(df) - len(df_clean)
        print(f"🧹 Z-score outlier removal: {removed} outliers, {len(df_clean)} samples retained")
    else:  # IQR
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 2.5 * IQR
        upper = Q3 + 2.5 * IQR
        df_clean = df[(df['price'] >= lower) & (df['price'] <= upper)].copy()
        removed = len(df) - len(df_clean)
        print(f"🧹 IQR outlier removal: {removed} outliers, {len(df_clean)} samples retained")
    
    return df_clean


def train_ensemble(X_train, y_train, category):
    """Train ensemble models with hyperparameters from documentation"""
    print("🤖 Training ensemble models...")
    
    # XGBoost
    print("   Training XGBoost...")
    xgb = XGBRegressor(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=12 if category != 'mobile' else 14,
        min_child_weight=1,
        subsample=0.85,
        colsample_bytree=0.85,
        gamma=0.01,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        verbosity=0
    )
    xgb.fit(X_train, y_train)
    
    # LightGBM
    print("   Training LightGBM...")
    lgb = LGBMRegressor(
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
        verbose=-1
    )
    lgb.fit(X_train, y_train)
    
    # Random Forest
    print("   Training RandomForest...")
    rf = RandomForestRegressor(
        n_estimators=500,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    # Gradient Boosting
    print("   Training GradientBoost...")
    gb = GradientBoostingRegressor(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=10,
        min_samples_split=15,
        min_samples_leaf=5,
        subsample=0.85,
        random_state=42
    )
    gb.fit(X_train, y_train)
    
    # Ensemble dictionary
    ensemble = {
        'xgb': xgb,
        'lgb': lgb,
        'rf': rf,
        'gb': gb,
        'weights': [0.35, 0.35, 0.15, 0.15]
    }
    
    return ensemble


def evaluate_model(ensemble, scaler, X_test, y_test):
    """Evaluate ensemble model"""
    # Scale test data
    X_test_scaled = scaler.transform(X_test)
    
    # Weighted ensemble prediction
    models = [ensemble['xgb'], ensemble['lgb'], ensemble['rf'], ensemble['gb']]
    weights = ensemble['weights']
    
    predictions = np.zeros(len(X_test))
    for model, weight in zip(models, weights):
        predictions += model.predict(X_test_scaled) * weight
    
    # Metrics
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    median_ae = median_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
    
    # Accuracy within ranges
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


def train_category(category: str, csv_path: str, outlier_method='zscore'):
    """Train model for a category"""
    print(f"\n{'='*80}")
    print(f"🔥 TRAINING {category.upper()} MODEL WITH NLP EXTRACTION")
    print(f"{'='*80}")
    
    # Load and extract features
    df = load_and_extract_features(csv_path, category)
    
    # Remove outliers
    df = remove_outliers(df, method=outlier_method)
    
    # Separate features and target
    X = df.drop('price', axis=1)
    y = df['price']
    
    print(f"✅ Final dataset: {len(X)} samples, {len(X.columns)} features")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"📊 Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Scale features
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train ensemble
    ensemble = train_ensemble(X_train_scaled, y_train, category)
    
    # Evaluate
    print("📊 Evaluating model...")
    metrics = evaluate_model(ensemble, scaler, X_test, y_test)
    
    # Print results
    print(f"\n{'='*80}")
    print(f"🔥 MODEL PERFORMANCE - {category.upper()}")
    print(f"{'='*80}")
    print(f"🏆 R² Score:        {metrics['r2_score']:.4f} ({metrics['r2_score']*100:.2f}%)")
    print(f"💰 MAE:             Rs. {metrics['mae']:,.2f}")
    print(f"📊 Median AE:       Rs. {metrics['median_ae']:,.2f}")
    print(f"📈 RMSE:            Rs. {metrics['rmse']:,.2f}")
    print(f"📉 MAPE:            {metrics['mape']:.2f}%")
    print(f"✅ Accuracy (±10%): {metrics['accuracy_10']:.2f}%")
    print(f"✅ Accuracy (±20%): {metrics['accuracy_20']:.2f}%")
    print(f"✅ Accuracy (±25%): {metrics['accuracy_25']:.2f}%")
    print(f"📦 Test Samples:    {len(X_test)}")
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
    
    print(f"💾 Models saved successfully!")
    
    return metrics


def main():
    print("\n" + "="*80)
    print("🚀 NLP-BASED MODEL TRAINING PIPELINE")
    print("Following PRICE_PREDICTION_DOCUMENTATION.md standards")
    print("="*80)
    
    scraped_dir = Path("scraped_data")
    
    # Find preprocessed files
    mobile_file = scraped_dir / "mobile_preprocessed_20251213_new.csv"
    laptop_file = scraped_dir / "laptop_preprocessed_20251213_new.csv"
    furniture_file = scraped_dir / "furniture_preprocessed_20251213_new.csv"
    
    results = {}
    
    # Train Mobile (Z-score outlier removal works better)
    if mobile_file.exists():
        results['mobile'] = train_category('mobile', str(mobile_file), outlier_method='zscore')
    
    # Train Laptop (IQR method)
    if laptop_file.exists():
        results['laptop'] = train_category('laptop', str(laptop_file), outlier_method='iqr')
    
    # Train Furniture (IQR method)
    if furniture_file.exists():
        results['furniture'] = train_category('furniture', str(furniture_file), outlier_method='iqr')
    
    # Summary
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE - SUMMARY")
    print("="*80)
    for cat, metrics in results.items():
        status = "✅" if metrics['r2_score'] > 0.70 else "⚠️"
        print(f"{status} {cat.upper()}: R²={metrics['r2_score']*100:.2f}% | MAE=Rs.{metrics['mae']:,.0f} | ±20%={metrics['accuracy_20']:.1f}%")
    print("="*80)


if __name__ == "__main__":
    main()
