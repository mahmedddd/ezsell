"""
Advanced ML Training Module with Hyperparameter Tuning
Trains price prediction models with multiple algorithms and ensemble methods
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor
import joblib
import logging
from pathlib import Path
from typing import Dict, Tuple, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PricePredictionTrainer:
    """Advanced trainer for price prediction models"""
    
    def __init__(self, category: str, output_dir: str = None):
        self.category = category
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent
        self.output_dir.mkdir(exist_ok=True)
        
        self.best_model = None
        self.best_score = float('-inf')
        self.feature_importance = None
        self.metrics = {}
        
    def train_multiple_models(self, X_train, y_train, X_test, y_test) -> Dict[str, Any]:
        """Train and compare multiple models"""
        logger.info(f"Training multiple models for {self.category} price prediction")
        
        models = {
            'Random Forest': RandomForestRegressor(random_state=42, n_jobs=-1),
            'Gradient Boosting': GradientBoostingRegressor(random_state=42),
            'XGBoost': XGBRegressor(random_state=42, n_jobs=-1),
            'Ridge': Ridge(random_state=42),
            'Lasso': Lasso(random_state=42)
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Calculate metrics
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, 
                                       scoring='r2', n_jobs=-1)
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            results[name] = {
                'model': model,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'accuracy_percent': test_r2 * 100
            }
            
            logger.info(f"{name} - Test R²: {test_r2:.4f}, MAE: {mae:.2f}, MAPE: {mape:.2f}%")
            
            # Track best model
            if test_r2 > self.best_score:
                self.best_score = test_r2
                self.best_model = model
        
        return results
    
    def hyperparameter_tuning(self, X_train, y_train, model_type: str = 'xgboost') -> Any:
        """Perform hyperparameter tuning"""
        logger.info(f"Starting hyperparameter tuning for {model_type}")
        
        if model_type == 'xgboost':
            param_dist = {
                'n_estimators': [100, 200, 300, 500],
                'max_depth': [3, 5, 7, 10],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0],
                'min_child_weight': [1, 3, 5],
                'gamma': [0, 0.1, 0.2]
            }
            base_model = XGBRegressor(random_state=42, n_jobs=-1)
            
        elif model_type == 'random_forest':
            param_dist = {
                'n_estimators': [100, 200, 300, 500],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['auto', 'sqrt', 'log2']
            }
            base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
            
        elif model_type == 'gradient_boosting':
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.05, 0.1],
                'subsample': [0.6, 0.8, 1.0],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            base_model = GradientBoostingRegressor(random_state=42)
        
        else:
            logger.warning(f"Unknown model type: {model_type}, using default XGBoost")
            return self.hyperparameter_tuning(X_train, y_train, 'xgboost')
        
        # Use RandomizedSearchCV for faster search
        random_search = RandomizedSearchCV(
            estimator=base_model,
            param_distributions=param_dist,
            n_iter=50,  # Number of parameter combinations to try
            cv=5,
            scoring='r2',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        logger.info("Running randomized search...")
        random_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def create_ensemble_model(self, X_train, y_train) -> StackingRegressor:
        """Create an ensemble model using stacking"""
        logger.info("Creating ensemble model with stacking")
        
        # Base models
        estimators = [
            ('rf', RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)),
            ('xgb', XGBRegressor(n_estimators=200, max_depth=7, learning_rate=0.1, random_state=42, n_jobs=-1)),
            ('gb', GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42))
        ]
        
        # Meta-learner
        stacking_model = StackingRegressor(
            estimators=estimators,
            final_estimator=Ridge(),
            cv=5,
            n_jobs=-1
        )
        
        logger.info("Training ensemble model...")
        stacking_model.fit(X_train, y_train)
        
        return stacking_model
    
    def train_best_model(self, X_train, y_train, X_test, y_test, 
                        use_tuning: bool = True, use_ensemble: bool = True) -> Tuple[Any, Dict]:
        """Train the best possible model"""
        logger.info("=" * 80)
        logger.info(f"TRAINING BEST MODEL FOR {self.category.upper()}")
        logger.info("=" * 80)
        
        # Step 1: Compare baseline models
        logger.info("\nStep 1: Comparing baseline models...")
        baseline_results = self.train_multiple_models(X_train, y_train, X_test, y_test)
        
        # Find best baseline
        best_baseline_name = max(baseline_results, key=lambda x: baseline_results[x]['test_r2'])
        best_baseline = baseline_results[best_baseline_name]
        logger.info(f"\nBest baseline model: {best_baseline_name}")
        logger.info(f"Baseline R²: {best_baseline['test_r2']:.4f}")
        logger.info(f"Baseline Accuracy: {best_baseline['accuracy_percent']:.2f}%")
        
        # Step 2: Hyperparameter tuning
        if use_tuning:
            logger.info("\nStep 2: Hyperparameter tuning...")
            tuned_models = {}
            
            for model_type in ['xgboost', 'random_forest', 'gradient_boosting']:
                try:
                    tuned_model = self.hyperparameter_tuning(X_train, y_train, model_type)
                    
                    # Evaluate tuned model
                    y_pred = tuned_model.predict(X_test)
                    test_r2 = r2_score(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
                    
                    tuned_models[model_type] = {
                        'model': tuned_model,
                        'test_r2': test_r2,
                        'mae': mae,
                        'rmse': rmse,
                        'mape': mape,
                        'accuracy_percent': test_r2 * 100
                    }
                    
                    logger.info(f"{model_type} tuned - R²: {test_r2:.4f}, Accuracy: {test_r2*100:.2f}%")
                    
                except Exception as e:
                    logger.error(f"Error tuning {model_type}: {e}")
            
            # Find best tuned model
            if tuned_models:
                best_tuned_name = max(tuned_models, key=lambda x: tuned_models[x]['test_r2'])
                best_tuned = tuned_models[best_tuned_name]
                
                logger.info(f"\nBest tuned model: {best_tuned_name}")
                logger.info(f"Tuned R²: {best_tuned['test_r2']:.4f}")
                logger.info(f"Tuned Accuracy: {best_tuned['accuracy_percent']:.2f}%")
                
                # Update best model if tuned is better
                if best_tuned['test_r2'] > best_baseline['test_r2']:
                    self.best_model = best_tuned['model']
                    self.best_score = best_tuned['test_r2']
        
        # Step 3: Ensemble model
        if use_ensemble:
            logger.info("\nStep 3: Creating ensemble model...")
            try:
                ensemble_model = self.create_ensemble_model(X_train, y_train)
                
                # Evaluate ensemble
                y_pred = ensemble_model.predict(X_test)
                test_r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
                
                logger.info(f"Ensemble R²: {test_r2:.4f}")
                logger.info(f"Ensemble Accuracy: {test_r2*100:.2f}%")
                
                # Update best model if ensemble is better
                if test_r2 > self.best_score:
                    self.best_model = ensemble_model
                    self.best_score = test_r2
                    
            except Exception as e:
                logger.error(f"Error creating ensemble: {e}")
        
        # Final evaluation
        logger.info("\n" + "=" * 80)
        logger.info("FINAL MODEL EVALUATION")
        logger.info("=" * 80)
        
        y_pred_train = self.best_model.predict(X_train)
        y_pred_test = self.best_model.predict(X_test)
        
        self.metrics = {
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'mae': mean_absolute_error(y_test, y_pred_test),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'mape': np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100,
            'accuracy_percent': r2_score(y_test, y_pred_test) * 100
        }
        
        logger.info(f"\nFinal Model Performance:")
        logger.info(f"  Training R²: {self.metrics['train_r2']:.4f}")
        logger.info(f"  Testing R²: {self.metrics['test_r2']:.4f}")
        logger.info(f"  MAE: Rs. {self.metrics['mae']:.2f}")
        logger.info(f"  RMSE: Rs. {self.metrics['rmse']:.2f}")
        logger.info(f"  MAPE: {self.metrics['mape']:.2f}%")
        logger.info(f"  ACCURACY: {self.metrics['accuracy_percent']:.2f}%")
        
        # Feature importance (if available)
        if hasattr(self.best_model, 'feature_importances_'):
            self.feature_importance = self.best_model.feature_importances_
        
        return self.best_model, self.metrics
    
    def save_model(self, model, feature_names: list, metrics: Dict):
        """Save trained model and metadata"""
        model_path = self.output_dir / f"price_predictor_{self.category}.pkl"
        metadata_path = self.output_dir / f"model_metadata_{self.category}.json"
        
        # Save model
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save metadata
        metadata = {
            'category': self.category,
            'feature_names': feature_names,
            'metrics': metrics,
            'feature_importance': self.feature_importance.tolist() if self.feature_importance is not None else None
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_path}")
    
    def train_pipeline(self, X, y, feature_names: list, test_size: float = 0.2) -> Dict:
        """Complete training pipeline"""
        logger.info(f"\nStarting training pipeline for {self.category}")
        logger.info(f"Dataset size: {len(X)} samples, {len(feature_names)} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Train best model
        model, metrics = self.train_best_model(
            X_train, y_train, X_test, y_test,
            use_tuning=True,
            use_ensemble=True
        )
        
        # Save model
        self.save_model(model, feature_names, metrics)
        
        return metrics
