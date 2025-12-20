"""
NLP and Keyword Extraction Service
Extracts meaningful keywords from text for recommendation system
"""
import re
from typing import List, Set, Dict
from collections import Counter
import json

class KeywordExtractor:
    """Extract keywords from text using NLP and regex patterns"""
    
    # Common stopwords to filter out
    STOPWORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'i', 'you', 'me', 'we', 'my', 'your',
        'this', 'these', 'those', 'am', 'been', 'being', 'have', 'had',
        'do', 'does', 'did', 'but', 'or', 'not', 'so', 'than', 'too', 'very',
        'can', 'just', 'should', 'now', 'get', 'got', 'want', 'need', 'used',
        'one', 'two', 'three', 'good', 'new', 'old', 'looking', 'buy', 'sell'
    }
    
    # Product-specific important terms
    IMPORTANT_TERMS = {
        # Electronics
        'laptop', 'mobile', 'phone', 'smartphone', 'tablet', 'computer', 'iphone',
        'samsung', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'macbook', 'ipad',
        'android', 'ios', 'gaming', 'processor', 'ram', 'storage', 'ssd', 'gb',
        
        # Furniture
        'furniture', 'sofa', 'chair', 'table', 'desk', 'bed', 'cabinet', 'wardrobe',
        'dining', 'bedroom', 'living', 'office', 'wooden', 'leather', 'fabric',
        
        # Vehicles
        'car', 'bike', 'motorcycle', 'vehicle', 'auto', 'honda', 'toyota', 'suzuki',
        'bmw', 'mercedes', 'audi', 'suv', 'sedan', 'hatchback',
        
        # Conditions
        'new', 'used', 'refurbished', 'excellent', 'good', 'fair', 'mint',
        
        # Brands (general)
        'apple', 'google', 'microsoft', 'sony', 'lg', 'xiaomi', 'oppo', 'vivo',
        'realme', 'oneplus', 'nokia'
    }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s-]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 15) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
        
        # Clean text
        cleaned = KeywordExtractor.clean_text(text)
        
        # Split into words
        words = cleaned.split()
        
        # Extract multi-word phrases (2-3 words)
        phrases = []
        for i in range(len(words) - 1):
            # 2-word phrases
            bigram = f"{words[i]} {words[i+1]}"
            if any(term in bigram for term in KeywordExtractor.IMPORTANT_TERMS):
                phrases.append(bigram)
            
            # 3-word phrases
            if i < len(words) - 2:
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if any(term in trigram for term in KeywordExtractor.IMPORTANT_TERMS):
                    phrases.append(trigram)
        
        # Filter single words
        filtered_words = [
            word for word in words
            if len(word) > 2  # Longer than 2 characters
            and word not in KeywordExtractor.STOPWORDS
            and not word.isdigit()  # Not just numbers
        ]
        
        # Prioritize important terms
        important_keywords = [
            word for word in filtered_words
            if word in KeywordExtractor.IMPORTANT_TERMS
        ]
        
        # Get word frequencies
        word_freq = Counter(filtered_words)
        common_words = [word for word, _ in word_freq.most_common(max_keywords)]
        
        # Combine and deduplicate
        keywords = []
        seen = set()
        
        # Add phrases first
        for phrase in phrases[:5]:  # Top 5 phrases
            if phrase not in seen:
                keywords.append(phrase)
                seen.add(phrase)
        
        # Add important terms
        for keyword in important_keywords:
            if keyword not in seen and len(keywords) < max_keywords:
                keywords.append(keyword)
                seen.add(keyword)
        
        # Add frequent words
        for keyword in common_words:
            if keyword not in seen and len(keywords) < max_keywords:
                keywords.append(keyword)
                seen.add(keyword)
        
        return keywords[:max_keywords]
    
    @staticmethod
    def extract_brand(text: str) -> str | None:
        """Extract brand name from text"""
        if not text:
            return None
        
        cleaned = KeywordExtractor.clean_text(text)
        
        # Define brand patterns
        brand_patterns = {
            'apple': r'\b(apple|iphone|ipad|macbook|airpods)\b',
            'samsung': r'\b(samsung|galaxy)\b',
            'dell': r'\bdell\b',
            'hp': r'\bhp\b',
            'lenovo': r'\blenovo\b',
            'asus': r'\basus\b',
            'acer': r'\bacer\b',
            'sony': r'\bsony\b',
            'lg': r'\blg\b',
            'xiaomi': r'\b(xiaomi|mi|redmi|poco)\b',
            'oppo': r'\boppo\b',
            'vivo': r'\bvivo\b',
            'realme': r'\brealme\b',
            'oneplus': r'\boneplus\b',
            'nokia': r'\bnokia\b',
            'google': r'\b(google|pixel)\b',
            'microsoft': r'\bmicrosoft\b',
            'honda': r'\bhonda\b',
            'toyota': r'\btoyota\b',
            'suzuki': r'\bsuzuki\b',
            'bmw': r'\bbmw\b',
            'mercedes': r'\b(mercedes|benz)\b',
            'audi': r'\baudi\b'
        }
        
        for brand, pattern in brand_patterns.items():
            if re.search(pattern, cleaned):
                return brand.capitalize()
        
        return None
    
    @staticmethod
    def extract_price_range(text: str) -> tuple[float | None, float | None]:
        """Extract price or price range from text"""
        if not text:
            return None, None
        
        # Find all numbers that could be prices
        price_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
            r'(\d+(?:,\d{3})*)\s*(?:dollars?|usd|pkr|rs)',  # 1000 dollars
            r'(?:price|cost|worth)\s*:?\s*(\d+(?:,\d{3})*)',  # price: 1000
            r'(\d+(?:,\d{3})*)\s*(?:to|-)\s*(\d+(?:,\d{3})*)',  # 1000 to 2000
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m:
                            try:
                                price = float(m.replace(',', ''))
                                if 10 < price < 10000000:  # Reasonable price range
                                    prices.append(price)
                            except ValueError:
                                pass
                else:
                    try:
                        price = float(match.replace(',', ''))
                        if 10 < price < 10000000:
                            prices.append(price)
                    except ValueError:
                        pass
        
        if not prices:
            return None, None
        
        return min(prices), max(prices)
    
    @staticmethod
    def categorize_text(text: str) -> str | None:
        """Automatically categorize text based on keywords"""
        if not text:
            return None
        
        cleaned = KeywordExtractor.clean_text(text)
        
        category_keywords = {
            'Electronics': ['laptop', 'mobile', 'phone', 'computer', 'tablet', 'smartphone', 
                          'electronic', 'device', 'gadget', 'iphone', 'android', 'processor'],
            'Furniture': ['furniture', 'sofa', 'chair', 'table', 'desk', 'bed', 'cabinet',
                        'wardrobe', 'dining', 'bedroom', 'wooden'],
            'Vehicles': ['car', 'bike', 'motorcycle', 'vehicle', 'auto', 'suv', 'sedan',
                       'hatchback', 'scooter', 'cycle'],
            'Fashion': ['clothing', 'shoes', 'dress', 'shirt', 'jeans', 'fashion', 'wear',
                       'jacket', 'sweater', 'accessories'],
            'Home & Garden': ['home', 'garden', 'appliance', 'kitchen', 'tools', 'decor',
                            'decoration', 'plants', 'outdoor']
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in cleaned)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None


def aggregate_keywords(keyword_lists: List[List[str]]) -> Dict[str, int]:
    """Aggregate multiple keyword lists with frequency counts"""
    all_keywords = []
    for keywords in keyword_lists:
        all_keywords.extend(keywords)
    
    return dict(Counter(all_keywords))


def calculate_keyword_similarity(keywords1: List[str], keywords2: List[str]) -> float:
    """Calculate similarity between two keyword lists (Jaccard similarity)"""
    if not keywords1 or not keywords2:
        return 0.0
    
    set1 = set(keywords1)
    set2 = set(keywords2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0
