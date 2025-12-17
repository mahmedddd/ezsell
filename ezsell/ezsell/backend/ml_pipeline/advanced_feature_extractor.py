"""
Advanced Feature Extraction using NLP and Regex
Extracts maximum information from titles and descriptions
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedFeatureExtractor:
    """Extract features from text using NLP and regex patterns"""
    
    # Brand dictionaries
    MOBILE_BRANDS = [
        'samsung', 'apple', 'iphone', 'xiaomi', 'redmi', 'oppo', 'vivo', 'realme',
        'oneplus', 'huawei', 'honor', 'nokia', 'motorola', 'google', 'pixel',
        'infinix', 'tecno', 'itel', 'sony', 'lg', 'asus', 'lenovo', 'blackberry'
    ]
    
    LAPTOP_BRANDS = [
        'dell', 'hp', 'lenovo', 'asus', 'acer', 'apple', 'macbook', 'msi',
        'razer', 'alienware', 'microsoft', 'surface', 'toshiba', 'sony', 'vaio',
        'samsung', 'lg', 'huawei', 'honor', 'thinkpad'
    ]
    
    FURNITURE_TYPES = [
        'sofa', 'couch', 'bed', 'table', 'chair', 'cabinet', 'wardrobe', 'dresser',
        'desk', 'shelf', 'bookshelf', 'dining', 'coffee table', 'nightstand',
        'armchair', 'recliner', 'ottoman', 'bench', 'stool', 'drawers'
    ]
    
    FURNITURE_MATERIALS = [
        'wood', 'wooden', 'oak', 'pine', 'teak', 'mahogany', 'walnut',
        'metal', 'steel', 'iron', 'aluminum', 'brass',
        'leather', 'fabric', 'velvet', 'cotton', 'linen',
        'glass', 'marble', 'plastic', 'rattan', 'wicker'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ==================== MOBILE EXTRACTION ====================
    
    def extract_mobile_features(self, text: str) -> Dict:
        """Extract all possible mobile features from text"""
        text = str(text).lower()
        features = {}
        
        # RAM (more patterns)
        ram_patterns = [
            r'(\d+)\s*gb\s*ram',
            r'ram\s*(\d+)\s*gb',
            r'(\d+)gb\s*ram',
            r'(\d+)\s*g\s*ram',
            r'memory\s*(\d+)\s*gb'
        ]
        features['ram'] = self._extract_first_match(text, ram_patterns)
        
        # Storage (multiple patterns)
        storage_patterns = [
            r'(\d+)\s*gb(?!\s*ram)',
            r'(\d+)\s*tb',
            r'storage\s*(\d+)\s*gb',
            r'(\d+)gb\s*storage',
            r'internal\s*(\d+)\s*gb'
        ]
        storage = self._extract_first_match(text, storage_patterns)
        if storage and 'tb' in text:
            storage = storage * 1024
        features['storage'] = storage
        
        # Battery (mAh)
        battery_patterns = [
            r'(\d{4,5})\s*mah',
            r'battery\s*(\d{4,5})',
            r'(\d{4,5})\s*m\s*ah'
        ]
        features['battery'] = self._extract_first_match(text, battery_patterns)
        
        # Camera (MP)
        camera_patterns = [
            r'(\d+)\s*mp',
            r'camera\s*(\d+)',
            r'(\d+)\s*mega\s*pixel',
            r'(\d+)\s*megapixel'
        ]
        features['camera'] = self._extract_first_match(text, camera_patterns)
        
        # Screen size (inches)
        screen_patterns = [
            r'(\d+\.?\d*)\s*inch',
            r'(\d+\.?\d*)\"',
            r'(\d+\.?\d*)\s*in\s',
            r'display\s*(\d+\.?\d*)'
        ]
        features['screen_size'] = self._extract_first_match(text, screen_patterns, is_float=True)
        
        # PTA status
        features['is_pta'] = 1 if any(x in text for x in ['pta', 'pta approved', 'approved']) else 0
        features['non_pta'] = 1 if any(x in text for x in ['non pta', 'non-pta', 'without pta']) else 0
        
        # Box & accessories
        features['with_box'] = 1 if any(x in text for x in ['with box', 'box pack', 'complete box']) else 0
        features['with_charger'] = 1 if 'charger' in text else 0
        features['with_accessories'] = 1 if any(x in text for x in ['accessories', 'complete package']) else 0
        
        # Warranty
        features['has_warranty'] = 1 if 'warranty' in text else 0
        
        # Display type
        features['is_amoled'] = 1 if any(x in text for x in ['amoled', 'super amoled', 'oled']) else 0
        features['is_lcd'] = 1 if 'lcd' in text else 0
        
        # Network
        features['is_5g'] = 1 if '5g' in text else 0
        features['is_4g'] = 1 if '4g' in text else 0
        
        # Condition keywords
        features['is_new'] = 1 if any(x in text for x in ['brand new', 'new', 'sealed', 'unopened']) else 0
        features['is_used'] = 1 if 'used' in text else 0
        features['condition_score'] = self._extract_condition_score(text)
        
        # Brand value (premium vs budget)
        features['brand_premium'] = self._get_mobile_brand_premium(text)
        
        # Model year
        features['model_year'] = self._extract_year(text)
        
        # Processor
        features['processor_type'] = self._extract_mobile_processor(text)
        
        return features
    
    # ==================== LAPTOP EXTRACTION ====================
    
    def extract_laptop_features(self, text: str) -> Dict:
        """Extract all possible laptop features from text"""
        text = str(text).lower()
        features = {}
        
        # Processor details (more comprehensive)
        processor_info = self._extract_laptop_processor_detailed(text)
        features.update(processor_info)
        
        # RAM
        ram_patterns = [
            r'(\d+)\s*gb\s*ram',
            r'ram\s*(\d+)\s*gb',
            r'(\d+)gb\s*ram',
            r'memory\s*(\d+)\s*gb'
        ]
        features['ram'] = self._extract_first_match(text, ram_patterns)
        
        # Storage with type
        storage_info = self._extract_storage_detailed(text)
        features.update(storage_info)
        
        # GPU
        gpu_info = self._extract_gpu_detailed(text)
        features.update(gpu_info)
        
        # Screen size
        screen_patterns = [
            r'(\d+\.?\d*)\s*inch',
            r'(\d+\.?\d*)\"',
            r'display\s*(\d+\.?\d*)'
        ]
        features['screen_size'] = self._extract_first_match(text, screen_patterns, is_float=True)
        
        # Screen resolution
        features['is_fullhd'] = 1 if any(x in text for x in ['1920x1080', 'full hd', 'fhd', '1080p']) else 0
        features['is_4k'] = 1 if any(x in text for x in ['4k', 'uhd', '3840x2160']) else 0
        features['is_2k'] = 1 if any(x in text for x in ['2k', 'qhd', '2560x1440']) else 0
        
        # Special features
        features['is_gaming'] = 1 if any(x in text for x in ['gaming', 'gamer', 'gaming laptop']) else 0
        features['is_touchscreen'] = 1 if 'touch' in text else 0
        features['is_2in1'] = 1 if any(x in text for x in ['2 in 1', '2-in-1', 'convertible']) else 0
        features['has_ssd'] = 1 if 'ssd' in text else 0
        features['has_hdd'] = 1 if any(x in text for x in ['hdd', 'hard disk', 'hard drive']) else 0
        
        # Battery
        battery_patterns = [
            r'(\d+)\s*wh',
            r'battery\s*(\d+)',
            r'(\d+)\s*hours?'
        ]
        features['battery_wh'] = self._extract_first_match(text, battery_patterns)
        
        # Condition
        features['is_new'] = 1 if any(x in text for x in ['brand new', 'new', 'sealed']) else 0
        features['is_used'] = 1 if 'used' in text else 0
        features['condition_score'] = self._extract_condition_score(text)
        
        # Warranty
        features['has_warranty'] = 1 if 'warranty' in text else 0
        
        # Brand premium
        features['brand_premium'] = self._get_laptop_brand_premium(text)
        
        # Model year
        features['model_year'] = self._extract_year(text)
        
        # Backlit keyboard
        features['has_backlit'] = 1 if any(x in text for x in ['backlit', 'backlight', 'illuminated']) else 0
        
        return features
    
    # ==================== FURNITURE EXTRACTION ====================
    
    def extract_furniture_features(self, text: str) -> Dict:
        """Extract all possible furniture features from text"""
        text = str(text).lower()
        features = {}
        
        # Type detection (more detailed)
        furniture_type = self._extract_furniture_type(text)
        features['furniture_type'] = furniture_type
        features['is_sofa'] = 1 if any(x in text for x in ['sofa', 'couch']) else 0
        features['is_bed'] = 1 if 'bed' in text else 0
        features['is_table'] = 1 if 'table' in text else 0
        features['is_chair'] = 1 if 'chair' in text else 0
        
        # Material
        material_info = self._extract_furniture_material_detailed(text)
        features.update(material_info)
        
        # Dimensions (length, width, height)
        dimensions = self._extract_dimensions(text)
        features.update(dimensions)
        
        # Seating capacity
        seating_patterns = [
            r'(\d+)\s*seater',
            r'seats?\s*(\d+)',
            r'capacity\s*(\d+)'
        ]
        features['seating_capacity'] = self._extract_first_match(text, seating_patterns)
        
        # Condition
        features['is_new'] = 1 if any(x in text for x in ['brand new', 'new', 'unused']) else 0
        features['is_used'] = 1 if 'used' in text else 0
        features['condition_score'] = self._extract_condition_score(text)
        
        # Brand presence
        features['has_brand'] = self._has_furniture_brand(text)
        
        # Special features
        features['is_imported'] = 1 if any(x in text for x in ['imported', 'import']) else 0
        features['is_handmade'] = 1 if any(x in text for x in ['handmade', 'hand made', 'hand crafted']) else 0
        features['is_antique'] = 1 if any(x in text for x in ['antique', 'vintage', 'classic']) else 0
        features['is_modern'] = 1 if any(x in text for x in ['modern', 'contemporary']) else 0
        
        # Cushions/pillows
        features['with_cushions'] = 1 if any(x in text for x in ['cushion', 'pillow']) else 0
        
        # Warranty
        features['has_warranty'] = 1 if 'warranty' in text else 0
        
        return features
    
    # ==================== HELPER METHODS ====================
    
    def _extract_first_match(self, text: str, patterns: List[str], is_float: bool = False) -> Optional[float]:
        """Extract first matching pattern"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1)) if is_float else int(match.group(1))
                    return value
                except:
                    continue
        return None
    
    def _extract_condition_score(self, text: str) -> int:
        """Extract condition score from 1-10"""
        # Look for explicit ratings
        rating_match = re.search(r'(\d+)/10', text)
        if rating_match:
            return int(rating_match.group(1))
        
        # Keyword-based scoring
        if any(x in text for x in ['brand new', 'sealed', 'unopened']):
            return 10
        elif any(x in text for x in ['excellent', 'mint', 'perfect', 'flawless']):
            return 9
        elif any(x in text for x in ['good', 'well maintained', 'clean']):
            return 7
        elif 'used' in text:
            return 5
        elif any(x in text for x in ['worn', 'damaged', 'scratched']):
            return 3
        return 5  # Default
    
    def _get_mobile_brand_premium(self, text: str) -> int:
        """Score brand premium (1-5)"""
        if any(x in text for x in ['iphone', 'apple']):
            return 5
        elif any(x in text for x in ['samsung', 'oneplus', 'google', 'pixel']):
            return 4
        elif any(x in text for x in ['xiaomi', 'oppo', 'vivo', 'realme']):
            return 3
        elif any(x in text for x in ['infinix', 'tecno', 'itel']):
            return 2
        return 1
    
    def _get_laptop_brand_premium(self, text: str) -> int:
        """Score laptop brand premium (1-5)"""
        if any(x in text for x in ['macbook', 'apple']):
            return 5
        elif any(x in text for x in ['alienware', 'razer', 'msi']):
            return 4
        elif any(x in text for x in ['dell', 'hp', 'lenovo', 'asus']):
            return 3
        elif any(x in text for x in ['acer', 'toshiba']):
            return 2
        return 1
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract model year"""
        year_match = re.search(r'20(\d{2})', text)
        if year_match:
            year = int('20' + year_match.group(1))
            if 2015 <= year <= 2025:
                return year
        return None
    
    def _extract_mobile_processor(self, text: str) -> int:
        """Extract processor score"""
        if any(x in text for x in ['snapdragon', 'sd']):
            # Extract snapdragon number
            match = re.search(r'(?:snapdragon|sd)\s*(\d+)', text)
            if match:
                num = int(match.group(1))
                if num >= 800:
                    return 5
                elif num >= 700:
                    return 4
                elif num >= 600:
                    return 3
                return 2
        elif any(x in text for x in ['mediatek', 'helio', 'dimensity']):
            return 3
        elif any(x in text for x in ['a15', 'a14', 'a13']):  # Apple
            return 5
        return 2
    
    def _extract_laptop_processor_detailed(self, text: str) -> Dict:
        """Extract detailed processor info"""
        features = {}
        
        # Intel processors
        if 'core i9' in text or 'i9' in text:
            features['processor_tier'] = 5
            features['processor_brand'] = 1  # Intel
        elif 'core i7' in text or 'i7' in text:
            features['processor_tier'] = 4
            features['processor_brand'] = 1
        elif 'core i5' in text or 'i5' in text:
            features['processor_tier'] = 3
            features['processor_brand'] = 1
        elif 'core i3' in text or 'i3' in text:
            features['processor_tier'] = 2
            features['processor_brand'] = 1
        # AMD processors
        elif 'ryzen 9' in text:
            features['processor_tier'] = 5
            features['processor_brand'] = 2  # AMD
        elif 'ryzen 7' in text:
            features['processor_tier'] = 4
            features['processor_brand'] = 2
        elif 'ryzen 5' in text:
            features['processor_tier'] = 3
            features['processor_brand'] = 2
        # Apple
        elif any(x in text for x in ['m1', 'm2', 'm3']):
            features['processor_tier'] = 5
            features['processor_brand'] = 3  # Apple Silicon
        else:
            features['processor_tier'] = 2
            features['processor_brand'] = 0
        
        # Generation
        gen_match = re.search(r'(\d+)(?:th|st|nd|rd)\s*gen', text)
        if gen_match:
            features['processor_generation'] = int(gen_match.group(1))
        else:
            features['processor_generation'] = 0
        
        return features
    
    def _extract_storage_detailed(self, text: str) -> Dict:
        """Extract storage with type"""
        features = {}
        
        # Storage amount
        storage_match = re.search(r'(\d+)\s*(?:gb|tb)(?:\s*(?:ssd|hdd|nvme))?', text)
        if storage_match:
            storage = int(storage_match.group(1))
            if 'tb' in text:
                storage = storage * 1024
            features['storage'] = storage
        else:
            features['storage'] = None
        
        # Storage type score
        if 'nvme' in text or 'nvme ssd' in text:
            features['storage_type_score'] = 3
        elif 'ssd' in text:
            features['storage_type_score'] = 2
        elif 'hdd' in text:
            features['storage_type_score'] = 1
        else:
            features['storage_type_score'] = 0
        
        return features
    
    def _extract_gpu_detailed(self, text: str) -> Dict:
        """Extract GPU information"""
        features = {}
        
        # NVIDIA
        if 'rtx' in text:
            match = re.search(r'rtx\s*(\d{4})', text)
            if match:
                gpu_model = int(match.group(1))
                if gpu_model >= 4000:
                    features['gpu_tier'] = 5
                elif gpu_model >= 3000:
                    features['gpu_tier'] = 4
                elif gpu_model >= 2000:
                    features['gpu_tier'] = 3
                else:
                    features['gpu_tier'] = 2
            else:
                features['gpu_tier'] = 3
            features['has_dedicated_gpu'] = 1
        elif 'gtx' in text:
            features['gpu_tier'] = 2
            features['has_dedicated_gpu'] = 1
        # AMD
        elif any(x in text for x in ['radeon', 'rx']):
            features['gpu_tier'] = 3
            features['has_dedicated_gpu'] = 1
        # Integrated
        elif any(x in text for x in ['intel hd', 'intel uhd', 'iris']):
            features['gpu_tier'] = 1
            features['has_dedicated_gpu'] = 0
        else:
            features['gpu_tier'] = 0
            features['has_dedicated_gpu'] = 0
        
        return features
    
    def _extract_furniture_type(self, text: str) -> int:
        """Extract furniture type as numeric"""
        type_map = {
            'sofa': 1, 'couch': 1,
            'bed': 2,
            'table': 3, 'dining table': 3,
            'chair': 4,
            'cabinet': 5, 'wardrobe': 5,
            'desk': 6,
            'shelf': 7, 'bookshelf': 7
        }
        
        for keyword, value in type_map.items():
            if keyword in text:
                return value
        return 0
    
    def _extract_furniture_material_detailed(self, text: str) -> Dict:
        """Extract furniture material info"""
        features = {}
        
        # Material type
        if any(x in text for x in ['teak', 'oak', 'mahogany', 'walnut']):
            features['material_quality'] = 5
            features['material_type'] = 1  # Premium wood
        elif any(x in text for x in ['wood', 'wooden', 'pine']):
            features['material_quality'] = 3
            features['material_type'] = 1  # Wood
        elif any(x in text for x in ['leather', 'genuine leather']):
            features['material_quality'] = 4
            features['material_type'] = 2  # Leather
        elif any(x in text for x in ['fabric', 'velvet', 'cotton']):
            features['material_quality'] = 2
            features['material_type'] = 3  # Fabric
        elif any(x in text for x in ['metal', 'steel', 'iron']):
            features['material_quality'] = 3
            features['material_type'] = 4  # Metal
        else:
            features['material_quality'] = 2
            features['material_type'] = 0
        
        return features
    
    def _extract_dimensions(self, text: str) -> Dict:
        """Extract furniture dimensions"""
        features = {}
        
        # Pattern: 120x60x80 or 120 x 60 x 80
        dim_pattern = r'(\d+)\s*x\s*(\d+)(?:\s*x\s*(\d+))?'
        match = re.search(dim_pattern, text)
        
        if match:
            length = int(match.group(1))
            width = int(match.group(2))
            height = int(match.group(3)) if match.group(3) else 0
            
            features['length'] = length
            features['width'] = width
            features['height'] = height
            features['volume'] = length * width * height if height else length * width
        else:
            features['length'] = None
            features['width'] = None
            features['height'] = None
            features['volume'] = None
        
        return features
    
    def _has_furniture_brand(self, text: str) -> int:
        """Check if furniture has recognizable brand"""
        brands = ['ikea', 'habitt', 'interwood', 'master', 'chinioti', 'ansari']
        return 1 if any(brand in text for brand in brands) else 0
