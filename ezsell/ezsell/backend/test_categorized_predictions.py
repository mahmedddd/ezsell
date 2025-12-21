"""
🧪 Test Brand Categorization and Prediction Encoding
Test that dropdown values are properly encoded for accurate predictions
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_URL = "http://127.0.0.1:8000/api/v1"


def test_prediction(category: str, data: dict, expected_brand_score: int, test_name: str):
    """Test prediction with brand categorization"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}🔬 Test: {test_name}")
    print(f"{Fore.CYAN}{'='*70}")
    
    try:
        response = requests.post(
            f"{API_URL}/predict-price-with-dropdowns",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"{Fore.GREEN}✅ SUCCESS")
            print(f"\n{Fore.WHITE}📊 Input Data:")
            for key, value in data.items():
                if key != 'category':
                    print(f"   {key}: {Fore.CYAN}{value}")
            
            print(f"\n{Fore.WHITE}🎯 Prediction Results:")
            print(f"   Predicted Price: {Fore.GREEN}PKR {result['predicted_price']:,.2f}")
            print(f"   Confidence: {Fore.YELLOW}{result['confidence_score']*100:.2f}%")
            print(f"   Price Range: {Fore.BLUE}PKR {result['price_range_min']:,.2f} - PKR {result['price_range_max']:,.2f}")
            
            print(f"\n{Fore.WHITE}🔧 Extracted Features (Encoding Check):")
            extracted = result['extracted_features']
            
            # Check brand/material encoding
            if category == 'mobile' or category == 'laptop':
                actual_score = extracted.get('brand_premium', 0)
                print(f"   Brand: {data.get('brand')} → {Fore.MAGENTA}Score: {actual_score}")
                if abs(actual_score - expected_brand_score) <= 0.1:
                    print(f"   {Fore.GREEN}✓ Brand encoding correct!")
                else:
                    print(f"   {Fore.RED}✗ Brand encoding mismatch! Expected {expected_brand_score}, got {actual_score}")
            elif category == 'furniture':
                actual_score = extracted.get('material_quality', 0)
                print(f"   Material: {data.get('material')} → {Fore.MAGENTA}Score: {actual_score}")
                if abs(actual_score - expected_brand_score) <= 0.1:
                    print(f"   {Fore.GREEN}✓ Material encoding correct!")
                else:
                    print(f"   {Fore.RED}✗ Material encoding mismatch! Expected {expected_brand_score}, got {actual_score}")
            
            # Show other important features
            if 'ram' in extracted:
                print(f"   RAM: {Fore.CYAN}{extracted['ram']} GB")
            if 'storage' in extracted:
                print(f"   Storage: {Fore.CYAN}{extracted['storage']} GB")
            if 'condition_score' in extracted:
                print(f"   Condition: {data.get('condition')} → {Fore.MAGENTA}Score: {extracted['condition_score']}")
            
            return True
        else:
            print(f"{Fore.RED}❌ FAILED: {response.status_code}")
            print(f"{Fore.RED}{response.text}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ ERROR: {str(e)}")
        return False


def main():
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.YELLOW}🧪 Brand Categorization & Encoding Test Suite")
    print(f"{Fore.MAGENTA}{'='*70}")
    
    # Test Mobile - Premium Brand (Apple = 10)
    test_prediction(
        "mobile",
        {
            "category": "mobile",
            "brand": "Apple",
            "ram": 8,
            "storage": 256,
            "camera": 48,
            "battery": 4500,
            "screen_size": 6.1,
            "condition": "excellent",
            "age_months": 6,
            "has_5g": True,
            "has_pta": True,
            "has_amoled": True,
            "has_warranty": True,
            "has_box": True
        },
        expected_brand_score=10,
        test_name="Mobile - Premium Brand (Apple)"
    )
    
    # Test Mobile - Mid-Range Brand (Xiaomi = 6)
    test_prediction(
        "mobile",
        {
            "category": "mobile",
            "brand": "Xiaomi",
            "ram": 6,
            "storage": 128,
            "camera": 48,
            "battery": 5000,
            "screen_size": 6.4,
            "condition": "good",
            "age_months": 12,
            "has_5g": True,
            "has_pta": False,
            "has_amoled": False,
            "has_warranty": False,
            "has_box": False
        },
        expected_brand_score=6,
        test_name="Mobile - Mid-Range Brand (Xiaomi)"
    )
    
    # Test Mobile - Budget Brand (Infinix = 4)
    test_prediction(
        "mobile",
        {
            "category": "mobile",
            "brand": "Infinix",
            "ram": 4,
            "storage": 64,
            "camera": 13,
            "battery": 5000,
            "screen_size": 6.5,
            "condition": "good",
            "age_months": 6,
            "has_5g": False,
            "has_pta": False,
            "has_amoled": False,
            "has_warranty": False,
            "has_box": False
        },
        expected_brand_score=4,
        test_name="Mobile - Budget Brand (Infinix)"
    )
    
    # Test Laptop - Premium Brand (Apple MacBook = 10)
    test_prediction(
        "laptop",
        {
            "category": "laptop",
            "brand": "Apple",
            "processor": "M2",
            "generation": 13,
            "ram": 16,
            "storage": 512,
            "gpu": "None",
            "screen_size": 13.3,
            "condition": "excellent",
            "age_months": 12,
            "has_ssd": True,
            "is_gaming": False,
            "is_touchscreen": False
        },
        expected_brand_score=10,
        test_name="Laptop - Premium Brand (MacBook M2)"
    )
    
    # Test Laptop - High-End Brand (Dell = 7)
    test_prediction(
        "laptop",
        {
            "category": "laptop",
            "brand": "Dell",
            "processor": "i7",
            "generation": 11,
            "ram": 16,
            "storage": 512,
            "gpu": "RTX 3050",
            "screen_size": 15.6,
            "condition": "good",
            "age_months": 18,
            "has_ssd": True,
            "is_gaming": True,
            "is_touchscreen": False
        },
        expected_brand_score=7,
        test_name="Laptop - High-End Brand (Dell)"
    )
    
    # Test Laptop - Mid-Range Brand (Acer = 5)
    test_prediction(
        "laptop",
        {
            "category": "laptop",
            "brand": "Acer",
            "processor": "i5",
            "generation": 10,
            "ram": 8,
            "storage": 256,
            "gpu": "None",
            "screen_size": 15.6,
            "condition": "good",
            "age_months": 24,
            "has_ssd": True,
            "is_gaming": False,
            "is_touchscreen": False
        },
        expected_brand_score=5,
        test_name="Laptop - Mid-Range Brand (Acer)"
    )
    
    # Test Furniture - Premium Material (Teak = 9)
    test_prediction(
        "furniture",
        {
            "category": "furniture",
            "material": "Teak",
            "seating_capacity": 5,
            "length": 200,
            "width": 100,
            "height": 95,
            "condition": "excellent",
            "is_imported": True,
            "is_handmade": True,
            "has_storage": False,
            "is_modern": False,
            "is_antique": True
        },
        expected_brand_score=9,
        test_name="Furniture - Premium Material (Teak)"
    )
    
    # Test Furniture - Standard Material (Wood = 7)
    test_prediction(
        "furniture",
        {
            "category": "furniture",
            "material": "Wood",
            "seating_capacity": 3,
            "length": 150,
            "width": 80,
            "height": 85,
            "condition": "good",
            "is_imported": False,
            "is_handmade": False,
            "has_storage": True,
            "is_modern": True,
            "is_antique": False
        },
        expected_brand_score=7,
        test_name="Furniture - Standard Material (Wood)"
    )
    
    # Test Furniture - Budget Material (MDF = 5)
    test_prediction(
        "furniture",
        {
            "category": "furniture",
            "material": "MDF",
            "seating_capacity": 0,
            "length": 100,
            "width": 50,
            "height": 75,
            "condition": "fair",
            "is_imported": False,
            "is_handmade": False,
            "has_storage": False,
            "is_modern": True,
            "is_antique": False
        },
        expected_brand_score=5,
        test_name="Furniture - Budget Material (MDF)"
    )
    
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.GREEN}✅ Test Suite Complete!")
    print(f"{Fore.YELLOW}Backend: http://127.0.0.1:8000")
    print(f"{Fore.YELLOW}Frontend: http://localhost:8081")
    print(f"{Fore.MAGENTA}{'='*70}\n")


if __name__ == "__main__":
    main()
