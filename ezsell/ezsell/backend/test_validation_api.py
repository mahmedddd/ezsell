"""
Test Script for Price Prediction API with Validation
Run this to test all new endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_dropdown_options():
    """Test dropdown options endpoint"""
    print("\n=== TESTING DROPDOWN OPTIONS ===\n")
    
    for category in ['mobile', 'laptop', 'furniture']:
        response = requests.get(f"{BASE_URL}/dropdown-options/{category}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {category.upper()} Options:")
            print(f"  - Conditions: {len(data.get('condition', []))} options")
            print(f"  - Brands: {len(data.get('brands', []))} options")
            if 'boolean_features' in data:
                print(f"  - Boolean Features: {len(data['boolean_features'])} options")
        else:
            print(f"✗ Failed to get {category} options: {response.status_code}")
    print()


def test_validation_endpoint():
    """Test title validation endpoint"""
    print("\n=== TESTING TITLE VALIDATION ===\n")
    
    test_cases = [
        {
            'category': 'mobile',
            'title': 'Samsung Galaxy S23 Ultra 12GB RAM',
            'description': 'Brand new with warranty',
            'expected': True
        },
        {
            'category': 'mobile',
            'title': 'Phone for sale',
            'description': 'Good condition',
            'expected': False
        },
        {
            'category': 'laptop',
            'title': 'Dell XPS 15 i7 12th Gen 16GB RAM',
            'description': 'Gaming laptop',
            'expected': True
        },
        {
            'category': 'laptop',
            'title': 'Laptop good condition',
            'description': 'For sale',
            'expected': False
        },
        {
            'category': 'furniture',
            'title': 'Modern 5 Seater Sofa',
            'description': 'Premium quality',
            'material': 'Fabric',
            'expected': True
        },
        {
            'category': 'furniture',
            'title': 'Furniture for sale',
            'description': 'Good price',
            'material': '',
            'expected': False
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        params = {
            'category': test['category'],
            'title': test['title'],
            'description': test['description']
        }
        if 'material' in test:
            params['material'] = test['material']
        
        response = requests.post(f"{BASE_URL}/validate-title", params=params)
        
        if response.status_code == 200:
            result = response.json()
            is_valid = result.get('is_valid', False)
            
            if is_valid == test['expected']:
                status = "✓ PASS"
            else:
                status = "✗ FAIL"
            
            print(f"{status} Test {i}: {test['category']} - '{test['title']}'")
            print(f"  Expected: {test['expected']}, Got: {is_valid}")
            if not is_valid:
                print(f"  Message: {result.get('message', 'N/A')}")
        else:
            print(f"✗ Test {i} FAILED: HTTP {response.status_code}")
        print()


def test_prediction_valid():
    """Test prediction with valid title"""
    print("\n=== TESTING PREDICTION (VALID TITLE) ===\n")
    
    test_data = {
        'category': 'mobile',
        'title': 'Samsung Galaxy S23 Ultra 12GB RAM 256GB Storage',
        'description': 'Brand new Samsung Galaxy S23 Ultra with 12GB RAM, 256GB storage, 5000mAh battery. PTA approved.',
        'condition': 'new',
        'brand': 'Samsung',
        'ram': 12,
        'storage': 256
    }
    
    response = requests.post(f"{BASE_URL}/predict-price", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Prediction successful!")
        print(f"  Predicted Price: Rs. {result.get('predicted_price', 0):,.0f}")
        print(f"  Price Range: Rs. {result.get('confidence_lower', 0):,.0f} - Rs. {result.get('confidence_upper', 0):,.0f}")
        print(f"  Model Confidence: {result.get('model_confidence', 0):.2f}%")
        print(f"  Recommendation: {result.get('recommendation', 'N/A')}")
    else:
        print(f"✗ Prediction failed: HTTP {response.status_code}")
        print(f"  Error: {response.text}")
    print()


def test_prediction_invalid():
    """Test prediction with invalid title (should fail)"""
    print("\n=== TESTING PREDICTION (INVALID TITLE - SHOULD FAIL) ===\n")
    
    test_data = {
        'category': 'mobile',
        'title': 'Phone for sale',
        'description': 'Good phone with 8GB RAM',
        'condition': 'used',
        'ram': 8,
        'storage': 128
    }
    
    response = requests.post(f"{BASE_URL}/predict-price", json=test_data)
    
    if response.status_code == 422:
        print("✓ Validation correctly rejected invalid title!")
        error_detail = response.json().get('detail', {})
        print(f"  Error: {error_detail.get('error', 'N/A')}")
        print(f"  Message: {error_detail.get('message', 'N/A')}")
        if 'hints' in error_detail:
            print(f"  Example: {error_detail['hints'].get('example', 'N/A')}")
    else:
        print(f"✗ Expected 422 error, got: HTTP {response.status_code}")
    print()


def test_validation_hints():
    """Test validation hints endpoint"""
    print("\n=== TESTING VALIDATION HINTS ===\n")
    
    for category in ['mobile', 'laptop', 'furniture']:
        response = requests.get(f"{BASE_URL}/validation-hints/{category}")
        if response.status_code == 200:
            hints = response.json()
            print(f"✓ {category.upper()} Hints:")
            print(f"  Required: {hints.get('required', [])}")
            print(f"  Example: {hints.get('example', 'N/A')}")
        else:
            print(f"✗ Failed to get {category} hints")
    print()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 PRICE PREDICTION API VALIDATION TESTS")
    print("="*70)
    
    try:
        # Test all endpoints
        test_dropdown_options()
        test_validation_endpoint()
        test_validation_hints()
        test_prediction_valid()
        test_prediction_invalid()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETE")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server!")
        print("Please make sure the backend is running on http://localhost:8000")
        print("\nStart the backend with:")
        print("  cd backend")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
