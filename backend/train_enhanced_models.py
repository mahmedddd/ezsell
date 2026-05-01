"""
Enhanced ML Pipeline for Price Prediction
Trains models using merged datasets with advanced feature extraction
Target: >80% R² and >80% accuracy
"""

import pandas as pd
import numpy as np
import joblib
import warnings
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score, mean_absolute_error, median_absolute_error, mean_squared_error
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore')

# Import feature extractors
from ml_pipeline.advanced_feature_extractor import AdvancedFeatureExtractor


class EnhancedPricePredictionPipeline:
    """Complete pipeline for training enhanced price prediction models"""
    
    def __init__(self, output_dir='models_enhanced'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.feature_extractor = AdvancedFeatureExtractor()
        self.models = {}
        
    def train_mobile_model(self):
        """Train mobile price prediction model"""
        print("\n" + "="*80)
        print("📱 TRAINING MOBILE PRICE PREDICTION MODEL")
        print("="*80)
        
        # Load merged mobile dataset
        df = pd.read_csv('scraped_data/mobile_merged_all.csv')
        print(f"📂 Loaded {len(df):,} mobile listings")
        
        # Extract features for each row
        print("🔧 Extracting advanced features...")
        feature_list = []
        
        for idx, row in df.iterrows():
            try:
                features = self.feature_extractor.extract_mobile_features(row)
                features['price'] = row['Price']
                feature_list.append(features)
            except:
                continue
        
        feature_df = pd.DataFrame(feature_list)
        print(f"✅ Extracted {len(feature_df.columns)-1} features")
        
        # Prepare data
        X = feature_df.drop('price', axis=1)
        y = feature_df['price']
        
        # Remove outliers using IQR
        Q1, Q3 = y.quantile(0.25), y.quantile(0.75)
        IQR = Q3 - Q1
        mask = (y >= Q1 - 1.5*IQR) & (y <= Q3 + 1.5*IQR)
        X, y = X[mask], y[mask]
        print(f"🧹 After outlier removal: {len(X):,} samples")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Impute and scale
        imputer = SimpleImputer(strategy='median')
        scaler = RobustScaler()
        
        X_train_imp = imputer.fit_transform(X_train)
        X_test_imp = imputer.transform(X_test)
        X_train_scaled = scaler.fit_transform(X_train_imp)
        X_test_scaled = scaler.transform(X_test_imp)
        
        print(f"\n📊 Training: {len(X_train):,} | Test: {len(X_test):,}")
        print(f"💰 Price range: Rs.{y.min():,.0f} - Rs.{y.max():,.0f}")
        
        # Train ensemble
        print("\n🚀 Training ensemble...")
        model = self._train_ensemble(X_train_scaled, y_train)
        
        # Evaluate
        self._evaluate_model(model, X_test_scaled, y_test, 'Mobile')
        
        # Save
        self.models['mobile'] = {
            'model': model, 'imputer': imputer, 'scaler': scaler,
            'feature_names': list(X.columns)
        }
        joblib.dump(self.models['mobile'], 
                   self.output_dir / 'price_predictor_mobile_enhanced.pkl')
        print(f"\n💾 Model saved!")
        
        return model
    
    def train_laptop_model(self):
        """Train laptop price prediction model"""
        print("\n" + "="*80)
        print("💻 TRAINING LAPTOP PRICE PREDICTION MODEL")
        print("="*80)
        
        df = pd.read_csv('scraped_data/laptop_merged_all.csv')
        print(f"📂 Loaded {len(df):,} laptop listings")
        
        print("🔧 Extracting advanced features...")
        feature_list = []
        
        for idx, row in df.iterrows():
            try:
                features = self.feature_extractor.extract_laptop_features(row)
                features['price'] = row['Price']
                feature_list.append(features)
            except:
                continue
        
        feature_df = pd.DataFrame(feature_list)
        print(f"✅ Extracted {len(feature_df.columns)-1} features")
        
        X = feature_df.drop('price', axis=1)
        y = feature_df['price']
        
        Q1, Q3 = y.quantile(0.25), y.quantile(0.75)
        IQR = Q3 - Q1
        mask = (y >= Q1 - 1.5*IQR) & (y <= Q3 + 1.5*IQR)
        X, y = X[mask], y[mask]
        print(f"🧹 After outlier removal: {len(X):,} samples")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        imputer = SimpleImputer(strategy='median')
        scaler = RobustScaler()
        
        X_train_imp = imputer.fit_transform(X_train)
        X_test_imp = imputer.transform(X_test)
        X_train_scaled = scaler.fit_transform(X_train_imp)
        X_test_scaled = scaler.transform(X_test_imp)
        
        print(f"\n📊 Training: {len(X_train):,} | Test: {len(X_test):,}")
        print(f"💰 Price range: Rs.{y.min():,.0f} - Rs.{y.max():,.0f}")
        
        print("\n🚀 Training ensemble...")
        model = self._train_ensemble(X_train_scaled, y_train)
        
        self._evaluate_model(model, X_test_scaled, y_test, 'Laptop')
        
        self.models['laptop'] = {
            'model': model, 'imputer': imputer, 'scaler': scaler,
            'feature_names': list(X.columns)
        }
        joblib.dump(self.models['laptop'],
                   self.output_dir / 'price_predictor_laptop_enhanced.pkl')
        print(f"\n💾 Model saved!")
        
        return model
    
    def train_furniture_model(self):
        """Train furniture price prediction model"""
        print("\n" + "="*80)
        print("🛋️  TRAINING FURNITURE PRICE PREDICTION MODEL")
        print("="*80)
        
        df = pd.read_csv('scraped_data/furniture_merged_all.csv')
        print(f"📂 Loaded {len(df):,} furniture listings")
        
        print("🔧 Extracting advanced features...")
        feature_list = []
        
        for idx, row in df.iterrows():
            try:
                features = self.feature_extractor.extract_furniture_features(row)
                features['price'] = row['Price']
                feature_list.append(features)
            except:
                continue
        
        feature_df = pd.DataFrame(feature_list)
        print(f"✅ Extracted {len(feature_df.columns)-1} features")
        
        X = feature_df.drop('price', axis=1)
        y = feature_df['price']
        
        Q1, Q3 = y.quantile(0.25), y.quantile(0.75)
        IQR = Q3 - Q1
        mask = (y >= Q1 - 1.5*IQR) & (y <= Q3 + 1.5*IQR)
        X, y = X[mask], y[mask]
        print(f"🧹 After outlier removal: {len(X):,} samples")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        imputer = SimpleImputer(strategy='median')
        scaler = RobustScaler()
        
        X_train_imp = imputer.fit_transform(X_train)
        X_test_imp = imputer.transform(X_test)
        X_train_scaled = scaler.fit_transform(X_train_imp)
        X_test_scaled = scaler.transform(X_test_imp)
        
        print(f"\n📊 Training: {len(X_train):,} | Test: {len(X_test):,}")
        print(f"💰 Price range: Rs.{y.min():,.0f} - Rs.{y.max():,.0f}")
        
        print("\n🚀 Training ensemble...")
        model = self._train_ensemble(X_train_scaled, y_train)
        
        self._evaluate_model(model, X_test_scaled, y_test, 'Furniture')
        
        self.models['furniture'] = {
            'model': model, 'imputer': imputer, 'scaler': scaler,
            'feature_names': list(X.columns)
        }
        joblib.dump(self.models['furniture'],
                   self.output_dir / 'price_predictor_furniture_enhanced.pkl')
        print(f"\n💾 Model saved!")
        
        return model
    
    def _train_ensemble(self, X_train, y_train):
        """Train weighted ensemble of 4 models"""
        
        xgb_model = xgb.XGBRegressor(
            n_estimators=2000, learning_rate=0.02, max_depth=12,
            min_child_weight=1, subsample=0.85, colsample_bytree=0.85,
            gamma=0.01, reg_alpha=0.1, reg_lambda=2.0,
            random_state=42, n_jobs=-1, verbosity=0
        )
        
        lgb_model = lgb.LGBMRegressor(
            n_estimators=2000, learning_rate=0.02, max_depth=15,
            num_leaves=60, min_child_samples=15, subsample=0.85,
            colsample_bytree=0.85, reg_alpha=0.1, reg_lambda=2.0,
            random_state=42, n_jobs=-1, verbose=-1
        )
        
        rf_model = RandomForestRegressor(
            n_estimators=500, max_depth=20, min_samples_split=10,
            min_samples_leaf=4, max_features='sqrt',
            random_state=42, n_jobs=-1
        )
        
        gb_model = GradientBoostingRegressor(
            n_estimators=800, learning_rate=0.03, max_depth=10,
            min_samples_split=15, min_samples_leaf=5, subsample=0.85,
            random_state=42
        )
        
        print("   XGBoost...", end='')
        xgb_model.fit(X_train, y_train)
        print(" ✓")
        
        print("   LightGBM...", end='')
        lgb_model.fit(X_train, y_train)
        print(" ✓")
        
        print("   Random Forest...", end='')
        rf_model.fit(X_train, y_train)
        print(" ✓")
        
        print("   Gradient Boosting...", end='')
        gb_model.fit(X_train, y_train)
        print(" ✓")
        
        # Weighted ensemble
        class EnsembleModel:
            def __init__(self, xgb_m, lgb_m, rf_m, gb_m):
                self.xgb = xgb_m
                self.lgb = lgb_m
                self.rf = rf_m
                self.gb = gb_m
                self.weights = [0.35, 0.35, 0.15, 0.15]
            
            def predict(self, X):
                return (self.xgb.predict(X) * self.weights[0] +
                       self.lgb.predict(X) * self.weights[1] +
                       self.rf.predict(X) * self.weights[2] +
                       self.gb.predict(X) * self.weights[3])
        
        return EnsembleModel(xgb_model, lgb_model, rf_model, gb_model)
    
    def _evaluate_model(self, model, X_test, y_test, name):
        """Evaluate model performance"""
        print("\n" + "="*80)
        print(f"📊 {name.upper()} EVALUATION")
        print("="*80)
        
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        median_ae = median_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        acc_10 = np.mean(np.abs((y_test - y_pred) / y_test) <= 0.10) * 100
        acc_20 = np.mean(np.abs((y_test - y_pred) / y_test) <= 0.20) * 100
        acc_25 = np.mean(np.abs((y_test - y_pred) / y_test) <= 0.25) * 100
        
        print(f"\n🎯 Metrics:")
        print(f"   R² Score:      {r2:.4f} ({r2*100:.2f}%)")
        print(f"   MAE:           Rs. {mae:,.2f}")
        print(f"   Median AE:     Rs. {median_ae:,.2f}")
        print(f"   RMSE:          Rs. {rmse:,.2f}")
        print(f"   MAPE:          {mape:.2f}%")
        
        print(f"\n📈 Accuracy:")
        print(f"   ±10%:          {acc_10:.2f}%")
        print(f"   ±20%:          {acc_20:.2f}%")
        print(f"   ±25%:          {acc_25:.2f}%")
        
        if r2 >= 0.80 and acc_20 >= 80:
            status = "🏆 EXCELLENT"
        elif r2 >= 0.80 or acc_20 >= 70:
            status = "✅ GOOD"
        else:
            status = "⚠️  ACCEPTABLE"
        
        print(f"\n{status}")
        print(f"   Target: R²≥80% AND Acc@±20%≥80%")
        print(f"   Actual: R²={r2*100:.1f}% AND Acc@±20%={acc_20:.1f}%")


def main():
    """Main training pipeline"""
    print("\n" + "="*80)
    print("🚀 ENHANCED PRICE PREDICTION TRAINING")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: R²≥80% AND Accuracy@±20%≥80%")
    
    pipeline = EnhancedPricePredictionPipeline()
    
    results = {}
    
    try:
        pipeline.train_mobile_model()
        results['Mobile'] = '✅'
    except Exception as e:
        print(f"❌ Mobile failed: {e}")
        results['Mobile'] = '❌'
    
    try:
        pipeline.train_laptop_model()
        results['Laptop'] = '✅'
    except Exception as e:
        print(f"❌ Laptop failed: {e}")
        results['Laptop'] = '❌'
    
    try:
        pipeline.train_furniture_model()
        results['Furniture'] = '✅'
    except Exception as e:
        print(f"❌ Furniture failed: {e}")
        results['Furniture'] = '❌'
    
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE!")
    print("="*80)
    for cat, status in results.items():
        print(f"   {cat}: {status}")
    print(f"\n📁 models_enhanced/")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
