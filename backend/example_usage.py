"""
Example: How to Use the Trained Models in Production

This shows how to integrate the trained price prediction models
into your FastAPI application for real-time predictions.
"""

import joblib
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any


class PricePredictorAPI:
    """Production-ready price predictor"""
    
    def __init__(self, models_dir: str = None):
        self.models_dir = Path(models_dir) if models_dir else Path(__file__).parent
        self.models = {}
        self.metadata = {}
        self.load_models()
    
    def load_models(self):
        """Load all trained models"""
        categories = ['mobile', 'laptop', 'furniture']
        
        for category in categories:
            model_path = self.models_dir / f"price_predictor_{category}.pkl"
            metadata_path = self.models_dir / f"model_metadata_{category}.json"
            
            if model_path.exists():
                self.models[category] = joblib.load(model_path)
                print(f"✅ Loaded {category} model")
                
                if metadata_path.exists():
                    with open(metadata_path) as f:
                        self.metadata[category] = json.load(f)
                    print(f"   Accuracy: {self.metadata[category]['metrics']['accuracy_percent']:.2f}%")
            else:
                print(f"⚠️  {category} model not found at {model_path}")
    
    def predict_mobile_price(self, mobile_data: Dict[str, Any]) -> float:
        """
        Predict mobile phone price
        
        Args:
            mobile_data: Dictionary with keys:
                - brand: str (e.g., 'Samsung', 'Apple')
                - condition: str ('New' or 'Used')
                - ram: int (GB, e.g., 8)
                - storage: int (GB, e.g., 128)
                - battery: int (mAh, e.g., 4000)
                - screen_size: float (inches, e.g., 6.2)
                - camera: int (MP, e.g., 48)
        
        Returns:
            Predicted price in PKR
        """
        if 'mobile' not in self.models:
            raise ValueError("Mobile model not loaded")
        
        # Create DataFrame with required features
        df = pd.DataFrame([mobile_data])
        
        # Make prediction
        predicted_price = self.models['mobile'].predict(df)[0]
        
        return predicted_price
    
    def predict_laptop_price(self, laptop_data: Dict[str, Any]) -> float:
        """
        Predict laptop price
        
        Args:
            laptop_data: Dictionary with keys:
                - brand: str
                - condition: str
                - processor_type: str ('Intel', 'AMD', 'Apple')
                - generation: int (e.g., 11)
                - ram: int (GB)
                - storage: int (GB)
                - is_ssd: int (1 or 0)
                - has_gpu: int (1 or 0)
                - screen_size: float (inches)
        
        Returns:
            Predicted price in PKR
        """
        if 'laptop' not in self.models:
            raise ValueError("Laptop model not loaded")
        
        df = pd.DataFrame([laptop_data])
        predicted_price = self.models['laptop'].predict(df)[0]
        
        return predicted_price
    
    def predict_furniture_price(self, furniture_data: Dict[str, Any]) -> float:
        """
        Predict furniture price
        
        Args:
            furniture_data: Dictionary with keys:
                - type: str (e.g., 'Sofa', 'Bed')
                - condition: str
                - material: str (e.g., 'Wood', 'Fabric')
                - material_quality: int (1-5)
                - volume: float (cubic feet)
                - seating_capacity: int
                - size_score: float
                - capacity_score: float
                - age_factor: float (1.0 for new, 0.6 for used)
                - has_brand: int (1 or 0)
        
        Returns:
            Predicted price in PKR
        """
        if 'furniture' not in self.models:
            raise ValueError("Furniture model not loaded")
        
        df = pd.DataFrame([furniture_data])
        predicted_price = self.models['furniture'].predict(df)[0]
        
        return predicted_price
    
    def get_model_info(self, category: str) -> Dict:
        """Get model metadata and metrics"""
        if category in self.metadata:
            return self.metadata[category]
        return {}


# Example Usage
if __name__ == '__main__':
    # Initialize predictor
    predictor = PricePredictorAPI()
    
    print("\n" + "="*80)
    print("EXAMPLE PREDICTIONS")
    print("="*80)
    
    # Example 1: Predict Mobile Price
    if 'mobile' in predictor.models:
        print("\n📱 Mobile Phone Example:")
        mobile = {
            'brand': 'Samsung',
            'condition': 'Used',
            'ram': 8,
            'storage': 128,
            'battery': 4000,
            'screen_size': 6.2,
            'camera': 64,
            'ram_storage_ratio': 8/128,
            'capacity_score': (8*2 + 128 + 4000/1000),
            'age_factor': 0.7
        }
        
        price = predictor.predict_mobile_price(mobile)
        print(f"   Samsung Galaxy (8GB/128GB, Used)")
        print(f"   Predicted Price: Rs. {price:,.0f}")
    
    # Example 2: Predict Laptop Price
    if 'laptop' in predictor.models:
        print("\n💻 Laptop Example:")
        laptop = {
            'brand': 'Dell',
            'condition': 'Used',
            'processor_type': 'Intel',
            'generation': 11,
            'ram': 16,
            'storage': 512,
            'is_ssd': 1,
            'has_gpu': 1,
            'screen_size': 15.6,
            'ram_storage_ratio': 16/512,
            'capacity_score': (16*3 + 512/10),
            'processor_score': 11*10,
            'age_factor': 0.65
        }
        
        price = predictor.predict_laptop_price(laptop)
        print(f"   Dell (i7 11th Gen, 16GB/512GB SSD, Dedicated GPU)")
        print(f"   Predicted Price: Rs. {price:,.0f}")
    
    # Example 3: Predict Furniture Price
    if 'furniture' in predictor.models:
        print("\n🛋️  Furniture Example:")
        furniture = {
            'type': 'Sofa',
            'condition': 'New',
            'material': 'Fabric',
            'material_quality': 3,
            'volume': 50,  # cubic feet
            'seating_capacity': 5,
            'size_score': 3.9,  # log(50)
            'capacity_score': 5 * 3,
            'age_factor': 1.0,
            'has_brand': 0
        }
        
        price = predictor.predict_furniture_price(furniture)
        print(f"   5-Seater Fabric Sofa (New)")
        print(f"   Predicted Price: Rs. {price:,.0f}")
    
    print("\n" + "="*80)
    print("✅ Example predictions complete!")
    print("="*80)
