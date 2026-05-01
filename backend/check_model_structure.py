"""Check model structure"""
import joblib
from pathlib import Path

models_path = Path("trained_models")

for category in ["mobile", "laptop", "furniture"]:
    model_file = models_path / f"{category}_model.pkl"
    if model_file.exists():
        ensemble = joblib.load(model_file)
        print(f"\n{category.upper()} Model Structure:")
        print(f"Type: {type(ensemble)}")
        print(f"Keys: {ensemble.keys() if isinstance(ensemble, dict) else 'Not a dict'}")
        
        if isinstance(ensemble, dict):
            print(f"\nEnsemble keys detail:")
            for key in ensemble.keys():
                print(f"  - {key}: {type(ensemble[key])}")
