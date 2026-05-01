"""
Quick test to verify all trained models work correctly
"""

import sys
from pathlib import Path
import joblib
import json

def test_model(category: str):
    """Test a specific model"""
    print(f"\n{'='*80}")
    print(f"Testing {category.upper()} Model")
    print(f"{'='*80}")
    
    # Check if model file exists
    model_file = f"price_predictor_{category}.pkl"
    metadata_file = f"model_metadata_{category}.json"
    
    if not Path(model_file).exists():
        print(f"❌ Model file not found: {model_file}")
        return False
    
    if not Path(metadata_file).exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return False
    
    print(f"✅ Found model file: {model_file}")
    print(f"✅ Found metadata file: {metadata_file}")
    
    # Load model
    try:
        model = joblib.load(model_file)
        print(f"✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False
    
    # Load metadata
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"✅ Metadata loaded successfully")
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
        return False
    
    # Display metadata
    print(f"\n📊 Model Performance:")
    print(f"  - R² Score: {metadata['metrics']['test_r2']:.4f} ({metadata['metrics']['accuracy_percent']:.2f}%)")
    print(f"  - MAE: Rs. {metadata['metrics']['mae']:,.2f}")
    print(f"  - RMSE: Rs. {metadata['metrics']['rmse']:,.2f}")
    print(f"  - Features: {len(metadata['feature_names'])} features")
    print(f"  - Feature names: {', '.join(metadata['feature_names'])}")
    
    # Test prediction
    print(f"\n🧪 Testing prediction...")
    try:
        # Create dummy features
        num_features = len(metadata['feature_names'])
        test_features = [[1] * num_features]  # All features = 1 (simplified test)
        
        prediction = model.predict(test_features)
        print(f"✅ Prediction successful: Rs. {prediction[0]:,.2f}")
        print(f"   (Note: This is a test with dummy features)")
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False
    
    return True

def main():
    print("\n" + "="*80)
    print("🚀 ML MODEL VERIFICATION TEST")
    print("="*80)
    
    categories = ['mobile', 'laptop', 'furniture']
    results = {}
    
    for category in categories:
        results[category] = test_model(category)
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    all_passed = True
    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{category.capitalize()}: {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("\n🎉 ALL MODELS WORKING CORRECTLY!")
        print("\nYou can now:")
        print("1. Use the models via FastAPI endpoints: POST /predictions/predict")
        print("2. Load them in your code: joblib.load('price_predictor_mobile.pkl')")
        print("3. See example_usage.py for integration examples")
    else:
        print("\n⚠️ SOME MODELS FAILED - Please check the errors above")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
