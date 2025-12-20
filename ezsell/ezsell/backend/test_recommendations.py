"""
Test the Recommendation System
Run with: python test_recommendations.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOKEN = None  # Set your auth token here

def set_auth_headers():
    """Set authentication headers"""
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}"}
    return {}

def test_track_activity():
    """Test activity tracking"""
    print("\n=== Testing Activity Tracking ===")
    
    # Track search
    response = requests.post(
        f"{BASE_URL}/api/recommendations/track-activity",
        json={
            "activity_type": "search",
            "search_query": "iphone 13 pro max",
            "category": "Electronics"
        },
        headers=set_auth_headers()
    )
    print(f"Track search: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Track view
    response = requests.post(
        f"{BASE_URL}/api/recommendations/track-activity",
        json={
            "activity_type": "view",
            "listing_id": 1,
            "duration_seconds": 45
        },
        headers=set_auth_headers()
    )
    print(f"Track view: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_recommendations():
    """Test getting personalized recommendations"""
    print("\n=== Testing Personalized Recommendations ===")
    
    response = requests.get(
        f"{BASE_URL}/api/recommendations/personalized?limit=10",
        headers=set_auth_headers()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total recommendations: {data['total']}")
        
        for rec in data['recommendations'][:3]:
            print(f"\n- {rec['listing_details']['title']}")
            print(f"  Score: {rec['score']}")
            print(f"  Type: {rec['recommendation_type']}")
            print(f"  Reason: {rec['reason']}")
    else:
        print(f"Error: {response.text}")

def test_similar_listings():
    """Test getting similar listings"""
    print("\n=== Testing Similar Listings ===")
    
    response = requests.post(
        f"{BASE_URL}/api/recommendations/similar",
        json={
            "listing_id": 1,
            "limit": 5
        },
        headers=set_auth_headers()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total similar items: {data['total']}")
        
        for rec in data['recommendations']:
            print(f"\n- {rec['listing_details']['title']}")
            print(f"  Score: {rec['score']}")
            print(f"  Reason: {rec['reason']}")
    else:
        print(f"Error: {response.text}")

def test_trending():
    """Test getting trending listings"""
    print("\n=== Testing Trending Listings ===")
    
    response = requests.get(
        f"{BASE_URL}/api/recommendations/trending?limit=10"
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total trending items: {data['total']}")
        
        for rec in data['recommendations'][:5]:
            print(f"\n- {rec['listing_details']['title']}")
            print(f"  Type: {rec['recommendation_type']}")
    else:
        print(f"Error: {response.text}")

def test_dashboard():
    """Test user dashboard"""
    print("\n=== Testing User Dashboard ===")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/dashboard?days=30",
        headers=set_auth_headers()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nUser Metrics:")
        print(f"- Total Searches: {data['total_searches']}")
        print(f"- Total Views: {data['total_views']}")
        print(f"- Total Favorites: {data['total_favorites']}")
        print(f"- Engagement Score: {data['engagement_score']}/100")
        
        print(f"\nTop Categories:")
        for cat in data['top_categories'][:3]:
            print(f"- {cat['category']}: {cat['count']} ({cat['percentage']}%)")
        
        print(f"\nTop Keywords:")
        for kw in data['top_keywords'][:5]:
            print(f"- {kw['keyword']}: {kw['frequency']} (score: {kw['relevance_score']})")
        
        print(f"\nPrice Range: ${data['price_range']['min']} - ${data['price_range']['max']}")
    else:
        print(f"Error: {response.text}")

def test_user_interests():
    """Test getting user interests"""
    print("\n=== Testing User Interests ===")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/interests",
        headers=set_auth_headers()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Activities: {data['total_activities']}")
        print(f"Last Updated: {data['last_updated']}")
        
        print(f"\nCategories:")
        for cat, count in list(data['categories'].items())[:5]:
            print(f"- {cat}: {count}")
        
        print(f"\nTop Keywords:")
        for kw, count in list(data['keywords'].items())[:10]:
            print(f"- {kw}: {count}")
    else:
        print(f"Error: {response.text}")

def test_search_insights():
    """Test search insights"""
    print("\n=== Testing Search Insights ===")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/search-insights?days=7",
        headers=set_auth_headers()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nTop Searches:")
        for search in data['searches'][:5]:
            print(f"- '{search['query']}': {search['count']} times")
        
        print(f"\nTrending Categories:")
        for cat in data['trending_categories']:
            print(f"- {cat}")
        
        print(f"\nTrending Keywords:")
        for kw in data['trending_keywords'][:10]:
            print(f"- {kw}")
    else:
        print(f"Error: {response.text}")

def test_nlp_extraction():
    """Test NLP keyword extraction"""
    print("\n=== Testing NLP Keyword Extraction ===")
    
    from core.nlp_service import KeywordExtractor
    
    test_texts = [
        "Looking for iPhone 13 Pro Max 256GB in excellent condition",
        "Selling gaming laptop with RTX 3060 GPU and 16GB RAM",
        "Beautiful wooden dining table set with 6 chairs",
        "Honda Civic 2020 model, low mileage, well maintained"
    ]
    
    extractor = KeywordExtractor()
    
    for text in test_texts:
        print(f"\nText: {text}")
        keywords = extractor.extract_keywords(text)
        print(f"Keywords: {keywords}")
        
        brand = extractor.extract_brand(text)
        if brand:
            print(f"Brand: {brand}")
        
        category = extractor.categorize_text(text)
        if category:
            print(f"Category: {category}")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("RECOMMENDATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        # Test NLP (doesn't require server)
        test_nlp_extraction()
        
        # Test API endpoints (requires server running)
        test_track_activity()
        test_trending()
        test_similar_listings()
        test_get_recommendations()
        test_dashboard()
        test_user_interests()
        test_search_insights()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to server. Make sure the backend is running on port 8000.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # Instructions
    print("\nRECOMMENDATION SYSTEM TEST")
    print("=" * 60)
    print("1. Make sure the backend server is running: uvicorn main:app --reload")
    print("2. For authenticated tests, set your token in TOKEN variable")
    print("3. Some tests require existing listings in the database")
    print("=" * 60)
    
    run_all_tests()
