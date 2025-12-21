"""
🧠 NLP-Based Feature Extractor with Label Encoding
Production-ready feature extraction for price prediction
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPFeatureExtractor:
    """Advanced NLP-based feature extraction with label encoding"""
    
    def __init__(self):
        """Initialize feature extractor with label mappings"""
        
        # Brand mappings with premium scores (1-10)
        self.brand_mapping = {
            # Mobile brands
            'iphone': 10, 'apple': 10,
            'samsung': 8, 'galaxy': 8,
            'oneplus': 8, 'one plus': 8,
            'xiaomi': 6, 'redmi': 5, 'poco': 6, 'mi': 6,
            'oppo': 6, 'vivo': 6, 'realme': 5,
            'huawei': 7, 'honor': 6,
            'nokia': 5, 'motorola': 5, 'moto': 5,
            'infinix': 4, 'tecno': 4, 'itel': 3,
            'google': 9, 'pixel': 9,
            'sony': 7, 'lg': 6,
            # Laptop brands
            'macbook': 10, 'mac': 10,
            'dell': 7, 'hp': 6, 'lenovo': 7,
            'asus': 7, 'acer': 5, 'msi': 8,
            'razer': 9, 'alienware': 9,
            'microsoft': 8, 'surface': 8,
            'thinkpad': 8, 'pavilion': 6,
            # Furniture brands
            'ikea': 7, 'hab': 8, 'interwood': 9,
            'master': 7, 'chinioti': 8,
        }
        
        # Condition mappings (1-6 scale)
        self.condition_mapping = {
            'new': 6, 'brand new': 6, 'sealed': 6, 'boxed': 6, 'box packed': 6,
            'excellent': 5, 'mint': 5, 'like new': 5, '10/10': 5, '9/10': 5,
            'good': 4, 'very good': 4, '8/10': 4, '7/10': 4,
            'fair': 3, 'used': 3, '6/10': 3, '5/10': 3,
            'poor': 2, 'damaged': 2, 'faulty': 2, '4/10': 2,
            'for parts': 1, 'not working': 1,
        }
        
        # Processor tier mapping (1-10)
        self.processor_mapping = {
            'i3': 3, 'core i3': 3, 'i3-': 3,
            'i5': 5, 'core i5': 5, 'i5-': 5,
            'i7': 7, 'core i7': 7, 'i7-': 7,
            'i9': 9, 'core i9': 9, 'i9-': 9,
            'ryzen 3': 3, 'r3': 3,
            'ryzen 5': 5, 'r5': 5,
            'ryzen 7': 7, 'r7': 7,
            'ryzen 9': 9, 'r9': 9,
            'celeron': 2, 'pentium': 2,
            'atom': 1, 'm1': 9, 'm2': 10, 'm3': 10,
        }
        
        # GPU tier mapping (0-10)
        self.gpu_mapping = {
            'rtx 4090': 10, 'rtx 4080': 10,
            'rtx 4070': 9, 'rtx 4060': 8,
            'rtx 3090': 9, 'rtx 3080': 9, 'rtx 3070': 8, 'rtx 3060': 7,
            'rtx 3050': 6, 'rtx 2080': 7, 'rtx 2070': 7, 'rtx 2060': 6,
            'gtx 1660': 5, 'gtx 1650': 5, 'gtx 1080': 6, 'gtx 1070': 6,
            'gtx 1060': 5, 'gtx 1050': 4,
            'mx550': 3, 'mx450': 3, 'mx350': 2, 'mx250': 2, 'mx150': 2,
            'integrated': 0, 'intel uhd': 0, 'intel hd': 0,
        }
        
        # Material quality mapping (1-10)
        self.material_mapping = {
            'teak': 9, 'sheesham': 9, 'walnut': 9,
            'oak': 8, 'mahogany': 8, 'cherry': 8,
            'wood': 7, 'wooden': 7, 'solid wood': 8,
            'engineered wood': 6, 'particle board': 4, 'mdf': 5,
            'metal': 6, 'steel': 6, 'iron': 6,
            'glass': 5, 'plastic': 3, 'foam': 2,
            'leather': 7, 'fabric': 5, 'velvet': 6,
        }
    
    def extract_brand_premium(self, text: str) -> int:
        """Extract brand and return premium score"""
        if not text:
            return 5
        text = str(text).lower()
        
        for brand, score in self.brand_mapping.items():
            if brand in text:
                return score
        return 5  # Default mid-range
    
    def extract_condition_score(self, text: str) -> int:
        """Extract condition and return score (1-6)"""
        if not text:
            return 4  # Default good condition
        text = str(text).lower()
        
        for condition, score in self.condition_mapping.items():
            if condition in text:
                return score
        
        # Check for 10/10 pattern
        rating_match = re.search(r'(\d+)/10', text)
        if rating_match:
            rating = int(rating_match.group(1))
            if rating >= 9:
                return 5
            elif rating >= 7:
                return 4
            elif rating >= 5:
                return 3
            else:
                return 2
        
        return 4  # Default good
    
    def extract_ram(self, text: str) -> int:
        """Extract RAM with NLP patterns"""
        if not text:
            return 4
        text = str(text).lower()
        
        # Pattern 1: "8GB RAM" or "8 GB RAM"
        ram_match = re.search(r'(\d+)\s*gb\s+ram', text)
        if ram_match:
            ram = int(ram_match.group(1))
            if ram in [2, 3, 4, 6, 8, 12, 16, 32]:
                return ram
        
        # Pattern 2: "8/128" format (RAM/Storage)
        slash_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*gb', text)
        if slash_match:
            potential_ram = int(slash_match.group(1))
            if potential_ram in [2, 3, 4, 6, 8, 12, 16, 32]:
                return potential_ram
        
        # Pattern 3: Standalone "8GB"
        for ram_size in [32, 16, 12, 8, 6, 4, 3, 2]:
            pattern = f'{ram_size}gb'
            if pattern in text.replace(' ', ''):
                # Make sure it's not storage
                if not re.search(f'{ram_size}gb.*?(128|256|512|1024)', text):
                    return ram_size
        
        return 4  # Default
    
    def extract_storage(self, text: str) -> int:
        """Extract storage with NLP patterns"""
        if not text:
            return 64
        text = str(text).lower()
        
        # Pattern 1: TB storage
        tb_match = re.search(r'(\d+)\s*tb', text)
        if tb_match:
            return int(tb_match.group(1)) * 1024
        
        # Pattern 2: "8/128" format (RAM/Storage)
        slash_match = re.search(r'(\d+)\s*(?:gb)?[\s/]+(\d+)\s*gb', text)
        if slash_match:
            potential_storage = int(slash_match.group(2))
            if potential_storage in [16, 32, 64, 128, 256, 512, 1024]:
                return potential_storage
        
        # Pattern 3: "128GB storage/ROM/internal"
        storage_match = re.search(r'(\d+)\s*gb\s*(?:storage|rom|internal|ssd|hdd)', text)
        if storage_match:
            storage = int(storage_match.group(1))
            if storage in [16, 32, 64, 128, 256, 512, 1024, 2048]:
                return storage
        
        # Pattern 4: Standalone storage numbers
        for size in [2048, 1024, 512, 256, 128, 64, 32, 16]:
            if f'{size}gb' in text.replace(' ', ''):
                return size
        
        return 64  # Default
    
    def extract_camera(self, text: str) -> int:
        """Extract camera megapixels"""
        if not text:
            return 0
        text = str(text).lower()
        
        # Pattern: "48MP" or "48 MP"
        match = re.search(r'(\d+)\s*mp', text)
        if match:
            mp = int(match.group(1))
            if 2 <= mp <= 200:
                return mp
        
        return 0
    
    def extract_battery(self, text: str) -> int:
        """Extract battery capacity (mAh)"""
        if not text:
            return 0
        text = str(text).lower()
        
        match = re.search(r'(\d{4,5})\s*mah', text)
        if match:
            mah = int(match.group(1))
            if 1000 <= mah <= 10000:
                return mah
        
        return 0
    
    def extract_screen_size(self, text: str) -> float:
        """Extract screen size in inches"""
        if not text:
            return 0
        text = str(text).lower()
        
        # Pattern: 6.1" or 6.1 inch
        match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\'|display|screen)', text)
        if match:
            size = float(match.group(1))
            if 3.0 <= size <= 30.0:
                return size
        
        return 0
    
    def extract_processor_tier(self, text: str) -> int:
        """Extract processor tier with NLP"""
        if not text:
            return 5
        text = str(text).lower()
        
        for proc, tier in self.processor_mapping.items():
            if proc in text:
                return tier
        
        return 5  # Default mid-tier
    
    def extract_generation(self, text: str) -> int:
        """Extract processor generation"""
        if not text:
            return 8
        text = str(text).lower()
        
        # Pattern 1: "10th gen" or "10th generation"
        gen_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*gen', text)
        if gen_match:
            gen = int(gen_match.group(1))
            if 1 <= gen <= 14:
                return gen
        
        # Pattern 2: i5-10210U format
        cpu_match = re.search(r'(?:i[3579]|ryzen\s*[3579])-(\d{1,2})', text)
        if cpu_match:
            gen = int(cpu_match.group(1)[0])  # First digit is generation
            if 1 <= gen <= 14:
                return gen
        
        return 8  # Default
    
    def extract_gpu_tier(self, text: str) -> int:
        """Extract GPU tier"""
        if not text:
            return 0
        text = str(text).lower()
        
        for gpu, tier in self.gpu_mapping.items():
            if gpu in text:
                return tier
        
        # Check for dedicated GPU keywords
        if any(keyword in text for keyword in ['nvidia', 'geforce', 'radeon', 'amd']):
            return 5  # Default mid-tier GPU
        
        return 0  # Integrated graphics
    
    def extract_material_quality(self, text: str) -> int:
        """Extract furniture material quality"""
        if not text:
            return 5
        text = str(text).lower()
        
        highest_quality = 0
        for material, quality in self.material_mapping.items():
            if material in text:
                highest_quality = max(highest_quality, quality)
        
        return highest_quality if highest_quality > 0 else 5
    
    def extract_seating_capacity(self, text: str) -> int:
        """Extract seating capacity"""
        if not text:
            return 0
        text = str(text).lower()
        
        # Pattern: "3 seater" or "3-seater"
        match = re.search(r'(\d+)\s*[-]?\s*seater', text)
        if match:
            seats = int(match.group(1))
            if 1 <= seats <= 12:
                return seats
        
        return 0
    
    def extract_dimensions(self, text: str) -> Dict[str, float]:
        """Extract furniture dimensions (L x W x H)"""
        if not text:
            return {'length': 0, 'width': 0, 'height': 0}
        
        text = str(text).lower()
        dimensions = {'length': 0, 'width': 0, 'height': 0}
        
        # Pattern: "120 x 80 x 90" or "120x80x90"
        match = re.search(r'(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)', text)
        if match:
            dimensions['length'] = float(match.group(1))
            dimensions['width'] = float(match.group(2))
            dimensions['height'] = float(match.group(3))
        
        return dimensions
    
    def extract_age_months(self, text: str) -> int:
        """Extract item age in months"""
        if not text:
            return 12
        text = str(text).lower()
        
        # Pattern 1: "6 months old" or "6 months used"
        months_match = re.search(r'(\d+)\s*months?', text)
        if months_match:
            months = int(months_match.group(1))
            if 0 <= months <= 120:
                return months
        
        # Pattern 2: "1 year old" or "2 years"
        years_match = re.search(r'(\d+)\s*years?', text)
        if years_match:
            years = int(years_match.group(1))
            if 0 <= years <= 10:
                return years * 12
        
        # Check keywords
        if any(keyword in text for keyword in ['new', 'brand new', 'sealed', 'box packed']):
            return 0
        
        return 12  # Default 1 year
    
    def extract_binary_features(self, text: str, keywords: List[str]) -> int:
        """Extract binary features (0/1) based on keywords"""
        if not text:
            return 0
        text = str(text).lower()
        
        return 1 if any(keyword in text for keyword in keywords) else 0
    
    def extract_mobile_features(self, title: str, description: str = "") -> Dict[str, Any]:
        """Extract all mobile phone features"""
        combined_text = f"{title} {description}".lower()
        
        features = {
            'brand_premium': self.extract_brand_premium(combined_text),
            'ram': self.extract_ram(combined_text),
            'storage': self.extract_storage(combined_text),
            'battery': self.extract_battery(combined_text),
            'camera': self.extract_camera(combined_text),
            'screen_size': self.extract_screen_size(combined_text),
            'is_5g': self.extract_binary_features(combined_text, ['5g', '5 g']),
            'is_pta': self.extract_binary_features(combined_text, ['pta', 'pta approved', 'approved']),
            'is_amoled': self.extract_binary_features(combined_text, ['amoled', 'oled', 'super amoled']),
            'has_warranty': self.extract_binary_features(combined_text, ['warranty', 'guarantee']),
            'has_box': self.extract_binary_features(combined_text, ['box', 'boxed', 'box pack', 'original box']),
            'condition_score': self.extract_condition_score(combined_text),
            'age_months': self.extract_age_months(combined_text),
        }
        
        return features
    
    def extract_laptop_features(self, title: str, description: str = "") -> Dict[str, Any]:
        """Extract all laptop features"""
        combined_text = f"{title} {description}".lower()
        
        features = {
            'brand_premium': self.extract_brand_premium(combined_text),
            'processor_tier': self.extract_processor_tier(combined_text),
            'generation': self.extract_generation(combined_text),
            'ram': self.extract_ram(combined_text),
            'storage': self.extract_storage(combined_text),
            'has_gpu': 1 if self.extract_gpu_tier(combined_text) > 0 else 0,
            'gpu_tier': self.extract_gpu_tier(combined_text),
            'is_gaming': self.extract_binary_features(combined_text, ['gaming', 'game', 'gamer']),
            'is_touchscreen': self.extract_binary_features(combined_text, ['touch', 'touchscreen', 'touch screen']),
            'has_ssd': self.extract_binary_features(combined_text, ['ssd', 'nvme', 'solid state']),
            'screen_size': self.extract_screen_size(combined_text),
            'condition_score': self.extract_condition_score(combined_text),
            'age_months': self.extract_age_months(combined_text),
        }
        
        return features
    
    def extract_furniture_features(self, title: str, description: str = "") -> Dict[str, Any]:
        """Extract all furniture features"""
        combined_text = f"{title} {description}".lower()
        dims = self.extract_dimensions(combined_text)
        
        features = {
            'material_quality': self.extract_material_quality(combined_text),
            'seating_capacity': self.extract_seating_capacity(combined_text),
            'length': dims['length'],
            'width': dims['width'],
            'height': dims['height'],
            'volume': dims['length'] * dims['width'] * dims['height'] if all(dims.values()) else 0,
            'is_imported': self.extract_binary_features(combined_text, ['import', 'imported', 'foreign']),
            'is_handmade': self.extract_binary_features(combined_text, ['handmade', 'hand made', 'handcrafted']),
            'has_storage': self.extract_binary_features(combined_text, ['storage', 'drawer', 'cabinet']),
            'is_modern': self.extract_binary_features(combined_text, ['modern', 'contemporary', 'minimalist']),
            'is_antique': self.extract_binary_features(combined_text, ['antique', 'vintage', 'classic']),
            'condition_score': self.extract_condition_score(combined_text),
        }
        
        return features
    
    def create_engineered_features(self, features: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Create engineered features based on category"""
        
        if category == 'mobile':
            # Performance score
            if 'ram' in features and 'storage' in features:
                features['performance'] = (features['ram'] ** 1.5) * (features['storage'] ** 0.5)
                features['ram_squared'] = features['ram'] ** 2
            
            # Depreciation factor
            if 'age_months' in features:
                features['depreciation'] = np.exp(-features['age_months'] / 24)
            
            # Brand-RAM interaction
            if 'brand_premium' in features and 'ram' in features:
                features['brand_ram'] = features['brand_premium'] * features['ram']
            
            # NO price_category - causes data leakage!
        
        elif category == 'laptop':
            # CPU score
            if 'processor_tier' in features and 'generation' in features:
                features['cpu_score'] = features['processor_tier'] * features['generation']
            
            # Memory score
            if 'ram' in features and 'storage' in features:
                features['memory_score'] = (features['ram'] ** 1.5) * (features['storage'] ** 0.5)
                features['ram_squared'] = features['ram'] ** 2
            
            # Gaming score
            if 'gpu_tier' in features:
                features['gaming_score'] = features['gpu_tier'] ** 2
            
            # Depreciation
            if 'age_months' in features:
                features['depreciation'] = np.exp(-features['age_months'] / 36)
            
            # NO price_category - causes data leakage!
        
        elif category == 'furniture':
            # Volume-based features
            if 'volume' in features and features['volume'] > 0:
                features['volume_log'] = np.log(features['volume'] + 1)
                
                # Size tier
                if features['volume'] < 500000:
                    features['size_tier'] = 1  # Small
                elif features['volume'] < 1000000:
                    features['size_tier'] = 2  # Medium
                else:
                    features['size_tier'] = 3  # Large
            else:
                features['volume_log'] = 0
                features['size_tier'] = 2
            
            # Quality score
            if 'material_quality' in features and 'condition_score' in features:
                features['quality'] = features['material_quality'] * features['condition_score']
            
            # Seating value
            if 'seating_capacity' in features and features['seating_capacity'] > 0:
                features['seating_value'] = features['seating_capacity'] ** 1.5
            else:
                features['seating_value'] = 0
            
            # NO price_category - causes data leakage!
        
        return features


# Singleton instance
_extractor = None

def get_feature_extractor() -> NLPFeatureExtractor:
    """Get singleton feature extractor"""
    global _extractor
    if _extractor is None:
        _extractor = NLPFeatureExtractor()
    return _extractor


if __name__ == "__main__":
    # Test the extractor
    extractor = NLPFeatureExtractor()
    
    # Test mobile
    mobile_features = extractor.extract_mobile_features(
        "Samsung Galaxy S21 5G 8GB RAM 128GB PTA Approved Excellent 10/10",
        "Brand new condition with 5000mAh battery and 48MP camera"
    )
    mobile_features = extractor.create_engineered_features(mobile_features, 'mobile')
    print("Mobile Features:")
    for k, v in mobile_features.items():
        print(f"  {k}: {v}")
    
    print("\n" + "="*80 + "\n")
    
    # Test laptop
    laptop_features = extractor.extract_laptop_features(
        "Dell Latitude Core i7 10th Gen 16GB RAM 512GB SSD Gaming Laptop",
        "NVIDIA GTX 1650 graphics card, touchscreen display"
    )
    laptop_features = extractor.create_engineered_features(laptop_features, 'laptop')
    print("Laptop Features:")
    for k, v in laptop_features.items():
        print(f"  {k}: {v}")
