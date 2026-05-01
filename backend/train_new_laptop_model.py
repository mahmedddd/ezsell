"""
Train laptop price prediction model on NEW high-quality dataset
"""
import pandas as pd
import pickle
import json
from sklearn.model_selection import train_test_split
from ml_pipeline.enhanced_preprocessor import EnhancedPreprocessor
from ml_pipeline.trainer import PricePredictionTrainer

def train_on_new_data():
    print("="*80)
    print("TRAINING ON NEW LAPTOP DATASET")
    print("="*80)
    
    # Load preprocessed data
    df = pd.read_csv('scraped_data/laptop_new_clean.csv')
    print(f"\nLoaded {len(df)} clean laptop records")
    print(f"Price range: Rs.{df['price'].min():,.0f} - Rs.{df['price'].max():,.0f}")
    print(f"Average price: Rs.{df['price'].mean():,.0f}")
    
    # Initialize preprocessor for feature engineering
    preprocessor = EnhancedPreprocessor()
    
    # Engineer features first (create composite scores)
    print("\n[Feature Engineering]")
    df_with_features = preprocessor._engineer_laptop_features(df)
    
    # Prepare features for training
    result = preprocessor.prepare_features(df_with_features, 'laptop')
    if len(result) == 3:
        X, feature_names, df_final = result
    else:
        X, feature_names = result
    
    y = df_with_features['price'].values
    
    print(f"Features prepared: {X.shape[1]} features")
    print(f"Training samples: {len(X)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train model
    print("\n[Training Best Model]")
    trainer = PricePredictionTrainer(category='laptop')
    model, metadata = trainer.train_best_model(X_train, y_train, X_test, y_test)
    
    # Save model
    model_path = 'models_enhanced/price_predictor_laptop_NEW.pkl'
    metadata_path = 'models_enhanced/model_metadata_laptop_NEW.json'
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Model saved to {model_path}")
    print(f"✓ Metadata saved to {metadata_path}")
    
    print("\n" + "="*80)
    print("FINAL MODEL PERFORMANCE")
    print("="*80)
    print(f"Accuracy: {metadata['accuracy']:.2f}%")
    print(f"R² Score: {metadata['r2_score']:.4f}")
    print(f"MAE: Rs.{metadata['mae']:,.2f}")
    print(f"RMSE: Rs.{metadata['rmse']:,.2f}")
    print(f"MAPE: {metadata['mape']:.2f}%")
    
    return model, metadata

if __name__ == "__main__":
    model, metadata = train_on_new_data()
