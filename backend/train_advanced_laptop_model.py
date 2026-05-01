"""
Advanced Laptop Model Training
Using improved features + ensemble methods + polynomial features
Target: 75%+ R²
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.ensemble import (
    RandomForestRegressor, 
    GradientBoostingRegressor,
    ExtraTreesRegressor,
    VotingRegressor,
    StackingRegressor
)
from sklearn.linear_model import Ridge, Lasso
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class AdvancedModelTrainer:
    """Advanced training with multiple algorithms and ensembling"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
        
    def prepare_features(self, df: pd.DataFrame):
        """Prepare feature matrix with advanced engineering"""
        
        # Select numeric features
        numeric_features = [
            'brand_score', 'ram', 'storage_gb', 'storage_score', 'is_ssd',
            'processor_tier', 'processor_brand', 'processor_generation', 'processor_score',
            'gpu_tier', 'has_dedicated_gpu', 'is_gaming_gpu', 'gpu_vram', 'gpu_score',
            'screen_size', 'is_fullhd', 'is_2k', 'is_4k', 'is_touchscreen', 'refresh_rate',
            'condition_score', 'is_new', 'is_used', 'has_warranty', 'age_years', 'age_penalty',
            'is_gaming', 'is_2in1', 'is_premium', 'has_backlit', 'has_fingerprint',
            'has_webcam', 'battery_wh', 'weight_kg',
            'text_length', 'word_count', 'total_specs_score'
        ]
        
        # Fill missing values intelligently
        X = df[numeric_features].copy()
        
        # Fill RAM with median
        if X['ram'].notna().sum() > 0:
            X['ram'].fillna(X['ram'].median(), inplace=True)
        else:
            X['ram'].fillna(8, inplace=True)
        
        # Fill storage with median
        if X['storage_gb'].notna().sum() > 0:
            X['storage_gb'].fillna(X['storage_gb'].median(), inplace=True)
        else:
            X['storage_gb'].fillna(256, inplace=True)
        
        # Fill GPU VRAM
        X['gpu_vram'].fillna(0, inplace=True)
        
        # Fill battery and weight
        X['battery_wh'].fillna(X['battery_wh'].median() if X['battery_wh'].notna().sum() > 0 else 45, inplace=True)
        X['weight_kg'].fillna(X['weight_kg'].median() if X['weight_kg'].notna().sum() > 0 else 2.0, inplace=True)
        
        # Fill remaining
        X.fillna(0, inplace=True)
        
        # Create additional engineered features
        X['ram_storage_ratio'] = X['ram'] / (X['storage_gb'] + 1)
        X['processor_gpu_combo'] = X['processor_score'] * X['gpu_score']
        X['premium_score'] = X['brand_score'] * X['condition_score'] * (X['is_premium'] + 1)
        X['gaming_score'] = X['is_gaming'] * (X['gpu_score'] + X['processor_score'])
        X['total_memory'] = X['ram'] + (X['gpu_vram'] * 2)
        X['specs_per_age'] = X['total_specs_score'] / (X['age_years'] + 1)
        X['value_indicator'] = (X['processor_score'] + X['ram'] * 5 + X['storage_gb'] / 10) * X['condition_score']
        
        return X.values
    
    def train_baseline_models(self, X_train, y_train, X_test, y_test):
        """Train baseline models and return best performers"""
        
        print("\n=== Training Baseline Models ===\n")
        
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=200, random_state=42),
            'Extra Trees': ExtraTreesRegressor(n_estimators=200, random_state=42, n_jobs=-1),
            'XGBoost': XGBRegressor(n_estimators=200, random_state=42, n_jobs=-1),
            'LightGBM': LGBMRegressor(n_estimators=200, random_state=42, n_jobs=-1, verbose=-1)
        }
        
        results = []
        for name, model in models.items():
            model.fit(X_train, y_train)
            
            train_score = r2_score(y_train, model.predict(X_train))
            test_score = r2_score(y_test, model.predict(X_test))
            mae = mean_absolute_error(y_test, model.predict(X_test))
            
            results.append({
                'name': name,
                'model': model,
                'train_r2': train_score,
                'test_r2': test_score,
                'mae': mae
            })
            
            print(f"{name:20s}: Train R²={train_score:.4f}, Test R²={test_score:.4f}, MAE=Rs.{mae:,.0f}")
        
        # Sort by test R²
        results.sort(key=lambda x: x['test_r2'], reverse=True)
        
        print(f"\n✓ Best baseline: {results[0]['name']} with {results[0]['test_r2']:.4f} R²")
        
        return results
    
    def tune_top_models(self, X_train, y_train, X_test, y_test, baseline_results):
        """Hyperparameter tuning for top 3 models"""
        
        print("\n=== Hyperparameter Tuning ===\n")
        
        top_models = baseline_results[:3]
        tuned_results = []
        
        for result in top_models:
            name = result['name']
            print(f"Tuning {name}...")
            
            if 'LightGBM' in name:
                param_grid = {
                    'num_leaves': [31, 50, 70],
                    'learning_rate': [0.01, 0.05, 0.1],
                    'n_estimators': [300, 500],
                    'max_depth': [10, 15, 20],
                    'min_child_samples': [10, 20, 30]
                }
                model = LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1)
            
            elif 'XGBoost' in name:
                param_grid = {
                    'max_depth': [5, 7, 10],
                    'learning_rate': [0.01, 0.05, 0.1],
                    'n_estimators': [300, 500],
                    'subsample': [0.7, 0.8, 0.9],
                    'colsample_bytree': [0.7, 0.8, 0.9]
                }
                model = XGBRegressor(random_state=42, n_jobs=-1)
            
            elif 'Gradient' in name:
                param_grid = {
                    'max_depth': [5, 7, 10],
                    'learning_rate': [0.01, 0.05, 0.1],
                    'n_estimators': [300, 500],
                    'subsample': [0.7, 0.8, 0.9],
                    'min_samples_split': [5, 10, 20]
                }
                model = GradientBoostingRegressor(random_state=42)
            
            elif 'Random Forest' in name:
                param_grid = {
                    'n_estimators': [300, 500],
                    'max_depth': [15, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
                model = RandomForestRegressor(random_state=42, n_jobs=-1)
            
            else:
                param_grid = {
                    'n_estimators': [300, 500],
                    'max_depth': [15, 20, None]
                }
                model = ExtraTreesRegressor(random_state=42, n_jobs=-1)
            
            # Grid search
            grid = GridSearchCV(
                model, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=0
            )
            grid.fit(X_train, y_train)
            
            best_model = grid.best_estimator_
            train_score = r2_score(y_train, best_model.predict(X_train))
            test_score = r2_score(y_test, best_model.predict(X_test))
            mae = mean_absolute_error(y_test, best_model.predict(X_test))
            
            tuned_results.append({
                'name': name,
                'model': best_model,
                'train_r2': train_score,
                'test_r2': test_score,
                'mae': mae,
                'params': grid.best_params_
            })
            
            print(f"  Best R²: {test_score:.4f} | Params: {grid.best_params_}")
        
        # Sort by test R²
        tuned_results.sort(key=lambda x: x['test_r2'], reverse=True)
        
        print(f"\n✓ Best tuned model: {tuned_results[0]['name']} with {tuned_results[0]['test_r2']:.4f} R²")
        
        return tuned_results
    
    def create_stacked_ensemble(self, X_train, y_train, X_test, y_test, tuned_results):
        """Create stacked ensemble with top models"""
        
        print("\n=== Building Stacked Ensemble ===\n")
        
        # Use top 3 as base estimators
        base_estimators = [
            (result['name'], result['model']) for result in tuned_results[:3]
        ]
        
        # Use Ridge as meta-learner
        meta_learner = Ridge(alpha=1.0)
        
        stacking = StackingRegressor(
            estimators=base_estimators,
            final_estimator=meta_learner,
            cv=5,
            n_jobs=-1
        )
        
        stacking.fit(X_train, y_train)
        
        train_score = r2_score(y_train, stacking.predict(X_train))
        test_score = r2_score(y_test, stacking.predict(X_test))
        mae = mean_absolute_error(y_test, stacking.predict(X_test))
        
        print(f"Stacked Ensemble: Train R²={train_score:.4f}, Test R²={test_score:.4f}, MAE=Rs.{mae:,.0f}")
        
        return {
            'name': 'Stacked Ensemble',
            'model': stacking,
            'train_r2': train_score,
            'test_r2': test_score,
            'mae': mae
        }
    
    def train(self, df: pd.DataFrame):
        """Main training pipeline"""
        
        print("=== Advanced Laptop Model Training ===\n")
        print(f"Dataset size: {len(df)} laptops")
        print(f"Price range: Rs.{df['price'].min():,.0f} - Rs.{df['price'].max():,.0f}")
        
        # Prepare features
        X = self.prepare_features(df)
        y = df['price'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"Feature matrix shape: {X_scaled.shape}")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        print(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
        
        # 1. Baseline models
        baseline_results = self.train_baseline_models(X_train, y_train, X_test, y_test)
        
        # 2. Tune top models
        tuned_results = self.tune_top_models(X_train, y_train, X_test, y_test, baseline_results)
        
        # 3. Stacked ensemble
        ensemble_result = self.create_stacked_ensemble(X_train, y_train, X_test, y_test, tuned_results)
        
        # Compare all
        all_results = tuned_results + [ensemble_result]
        all_results.sort(key=lambda x: x['test_r2'], reverse=True)
        
        best = all_results[0]
        
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"\n🏆 Best Model: {best['name']}")
        print(f"   Training R²:  {best['train_r2']:.4f}")
        print(f"   Testing R²:   {best['test_r2']:.4f}")
        print(f"   MAE:          Rs.{best['mae']:,.0f}")
        print(f"   RMSE:         Rs.{np.sqrt(mean_squared_error(y_test, best['model'].predict(X_test))):,.0f}")
        
        # Calculate MAPE
        y_pred = best['model'].predict(X_test)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        print(f"   MAPE:         {mape:.2f}%")
        
        if 'params' in best:
            print(f"\n   Best parameters:")
            for param, value in best['params'].items():
                print(f"      {param}: {value}")
        
        print("\n" + "="*60)
        
        return best['model'], self.scaler, best
    
    def save_model(self, model, scaler, metadata, filename='models_enhanced/price_predictor_laptop_ADVANCED.pkl'):
        """Save trained model"""
        
        model_data = {
            'model': model,
            'scaler': scaler,
            'metadata': metadata
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n✓ Model saved to {filename}")

if __name__ == '__main__':
    # Load advanced cleaned data
    df = pd.read_csv('scraped_data/laptop_advanced_clean.csv')
    
    print(f"\nLoaded {len(df)} laptop records")
    
    # Train
    trainer = AdvancedModelTrainer()
    model, scaler, metadata = trainer.train(df)
    
    # Save
    trainer.save_model(model, scaler, metadata)
    
    print("\n✅ Training complete!")
