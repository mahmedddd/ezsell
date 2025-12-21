"""
Title Validation Utility
Validates that titles contain relevant keywords for their category
Prevents irrelevant predictions by ensuring meaningful product information
"""

import re
from typing import Dict, List, Tuple

class TitleValidator:
    """Validates product titles based on category-specific requirements"""
    
    # Mobile phone brands and models
    MOBILE_BRANDS = {
        'apple', 'iphone', 'samsung', 'galaxy', 'xiaomi', 'redmi', 'mi', 'poco',
        'oppo', 'vivo', 'realme', 'oneplus', 'huawei', 'honor', 'nokia', 'motorola',
        'google', 'pixel', 'sony', 'xperia', 'asus', 'rog', 'lenovo', 'lg',
        'tecno', 'infinix', 'itel', 'qmobile', 'voice', 'spark', 'camon'
    }
    
    # Comprehensive brand-exclusive model keywords for mobiles
    MOBILE_BRAND_EXCLUSIVE = {
        'apple': {'iphone', 'se', 'mini', 'pro max'},
        'samsung': {'galaxy', 'note', 'fold', 'flip', 'a series', 'a0', 'a1', 'a2', 'a3', 'a5', 'a7', 'a8', 's series', 's20', 's21', 's22', 's23', 's24', 'z fold', 'z flip', 'm series', 'f series'},
        'xiaomi': {'redmi', 'poco', 'mi', 'mi note', 'mi mix', 'mi max'},
        'oppo': {'reno', 'find', 'find x', 'find n', 'a series', 'a3', 'a5', 'a7', 'a9', 'f series', 'k series'},
        'vivo': {'y series', 'v series', 'x series', 's series', 't series', 'nex', 'iqoo'},
        'realme': {'narzo', 'gt', 'x series', 'c series'},
        'oneplus': {'nord', 'oneplus ace', 'oneplus'},
        'google': {'pixel', 'pixel pro', 'pixel xl', 'pixel a'},
        'huawei': {'p series', 'mate', 'nova', 'p20', 'p30', 'p40', 'p50', 'mate 20', 'mate 30', 'mate 40'},
        'nokia': {'g series', 'c series', 'x series'},
        'motorola': {'moto g', 'moto e', 'edge', 'razr'},
        'sony': {'xperia'},
        'tecno': {'spark', 'camon', 'phantom', 'pova'},
        'infinix': {'note', 'hot', 'smart', 'zero'},
    }
    
    # Laptop brands and keywords
    LAPTOP_BRANDS = {
        'dell', 'hp', 'lenovo', 'asus', 'acer', 'apple', 'macbook', 'msi',
        'razer', 'alienware', 'thinkpad', 'ideapad', 'pavilion', 'envy',
        'inspiron', 'latitude', 'precision', 'elitebook', 'probook', 'vostro',
        'vivobook', 'zenbook', 'rog', 'tuf', 'gaming', 'predator', 'nitro',
        'surface', 'microsoft', 'samsung', 'lg', 'gram'
    }
    
    # Comprehensive brand-exclusive model keywords for laptops
    LAPTOP_BRAND_EXCLUSIVE = {
        'dell': {'inspiron', 'latitude', 'precision', 'xps', 'vostro', 'alienware'},
        'hp': {'pavilion', 'envy', 'elitebook', 'probook', 'omen', 'spectre', 'victus', 'zbook'},
        'lenovo': {'thinkpad', 'ideapad', 'yoga', 'legion', 'thinkbook'},
        'apple': {'macbook', 'macbook pro', 'macbook air', 'imac'},
        'asus': {'vivobook', 'zenbook', 'rog', 'tuf', 'expertbook', 'chromebook'},
        'acer': {'aspire', 'predator', 'nitro', 'swift', 'spin', 'travelmate'},
        'msi': {'katana', 'gf', 'gp', 'ge', 'gs', 'creator', 'prestige', 'modern', 'cyborg'},
        'razer': {'blade', 'blade stealth', 'blade pro'},
        'microsoft': {'surface', 'surface laptop', 'surface pro', 'surface book'},
        'samsung': {'galaxy book', 'notebook'},
        'lg': {'gram'},
    }
    
    LAPTOP_PROCESSORS = {
        'intel', 'core', 'i3', 'i5', 'i7', 'i9', 'pentium', 'celeron',
        'amd', 'ryzen', 'threadripper', 'athlon', 'apple', 'm1', 'm2', 'm3'
    }
    
    # Furniture types and keywords
    FURNITURE_TYPES = {
        'sofa', 'couch', 'chair', 'table', 'desk', 'bed', 'cabinet', 'wardrobe',
        'shelf', 'bookshelf', 'dresser', 'nightstand', 'dining', 'ottoman',
        'recliner', 'sectional', 'loveseat', 'bench', 'stool', 'armchair',
        'coffee table', 'side table', 'console', 'credenza', 'hutch', 'chest',
        'futon', 'mattress', 'headboard', 'frame', 'bunk', 'loft', 'daybed',
        'vanity', 'mirror', 'rack', 'stand', 'storage', 'organizer', 'drawer'
    }
    
    # Non-furniture keywords that should invalidate furniture listings
    NON_FURNITURE_KEYWORDS = {
        'phone', 'mobile', 'iphone', 'samsung', 'galaxy', 'xiaomi', 'oppo', 'vivo',
        'laptop', 'computer', 'macbook', 'dell', 'hp', 'lenovo', 'asus',
        'tablet', 'ipad', 'camera', 'tv', 'television', 'speaker', 'headphone',
        'watch', 'smartwatch', 'airpods', 'earbuds', 'charger', 'cable',
        'gaming console', 'playstation', 'xbox', 'nintendo', 'ps4', 'ps5',
        'ram', 'storage', 'processor', 'gpu', 'graphics card', 'motherboard'
    }
    
    FURNITURE_MATERIALS = {
        'wood', 'wooden', 'oak', 'pine', 'maple', 'walnut', 'teak', 'mahogany',
        'metal', 'steel', 'iron', 'aluminum', 'brass', 'leather', 'fabric',
        'velvet', 'linen', 'cotton', 'plastic', 'glass', 'marble', 'granite',
        'rattan', 'wicker', 'bamboo', 'mdf', 'plywood', 'veneer', 'laminate'
    }
    
    @classmethod
    def validate_mobile_title(cls, title: str, description: str = "") -> Tuple[bool, str, Dict]:
        """
        Validate mobile phone title contains brand information and check brand-model consistency
        Comprehensively validates that brand and model combinations are valid
        
        Returns:
            (is_valid, error_message, extracted_info)
        """
        text = f"{title} {description}".lower()
        
        # Check for any mobile brand keyword
        found_brands = [brand for brand in cls.MOBILE_BRANDS if brand in text]
        
        if not found_brands:
            return False, (
                "Mobile title must include a brand name (e.g., Samsung, iPhone, Xiaomi, Oppo, etc.)."
            ), {}
        
        # Comprehensive brand-model conflict detection
        # Check each brand's exclusive keywords against all other brands
        detected_brand = None
        conflicting_models = []
        
        # Determine primary brand
        for brand_key, exclusive_keywords in cls.MOBILE_BRAND_EXCLUSIVE.items():
            # Check if this brand is mentioned
            brand_mentioned = brand_key in text
            if brand_key == 'apple':
                brand_mentioned = 'apple' in text or 'iphone' in text
            elif brand_key == 'samsung':
                brand_mentioned = 'samsung' in text or 'galaxy' in text
            elif brand_key == 'xiaomi':
                brand_mentioned = any(x in text for x in ['xiaomi', 'redmi', 'poco', 'mi'])
                
            if brand_mentioned:
                detected_brand = brand_key
                break
        
        # If we detected a primary brand, check for conflicting models from other brands
        if detected_brand:
            for other_brand, other_keywords in cls.MOBILE_BRAND_EXCLUSIVE.items():
                if other_brand != detected_brand:
                    # Check if any exclusive keywords from other brands appear
                    # Use word boundary matching to avoid false positives (e.g., "one" in "iphone")
                    conflicts = []
                    for kw in other_keywords:
                        if len(kw) > 3:  # Only check keywords with 4+ chars
                            # Use word boundary regex to match whole words only
                            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                                conflicts.append(kw)
                    
                    # Filter out common generic terms
                    generic_terms = {'pro', 'max', 'plus', 'ultra', 'lite', 'note', 'mini', 'edge', 'a series', 'x series', 's series'}
                    significant_conflicts = [c for c in conflicts if c not in generic_terms]
                    
                    if significant_conflicts:
                        conflicting_models.extend([(other_brand, c) for c in significant_conflicts])
        
        # Report conflicts if found
        if conflicting_models:
            conflict_brand, conflict_model = conflicting_models[0]
            return False, (
                f"Invalid brand-model combination: '{detected_brand.title()}' cannot have '{conflict_model}' "
                f"(which is exclusive to {conflict_brand.title()}). "
                f"Please use correct brand and model name."
            ), {}
        
        # Extract model information (optional, not required)
        extracted = {
            'brands': found_brands,
            'detected_brand': detected_brand,
            'has_model_info': bool(re.search(r'\d+', text))
        }
        
        # Check for model/series information - require more than just brand name
        has_model_info = False
        
        # Check for model numbers (e.g., S23, A54, 14 Pro, Note 10)
        if re.search(r'\b\d+\b', text):
            has_model_info = True
        
        # Check for series names (but NOT brand names like 'iphone' alone)
        # These are valid series indicators ONLY when combined with numbers
        series_keywords = {
            'galaxy', 'redmi', 'poco', 'pixel', 'note', 'fold', 'flip', 
            'reno', 'find', 'narzo', 'nord', 'mate', 'nova', 'spark', 'camon',
            'hot', 'smart', 'phantom', 'pova', 'xperia', 'moto', 'edge', 'razr',
            'y series', 'v series', 'x series', 'a series', 's series', 'f series',
            'gt', 'pro', 'plus', 'ultra', 'max', 'mini', 'lite', 'se'
        }
        
        # iPhone requires a number (iPhone 14, iPhone 15, etc.) - "iphone" alone is not valid
        # Same for other brand-series names
        for keyword in series_keywords:
            if keyword in text:
                has_model_info = True
                break
        
        extracted['has_model_info'] = has_model_info
        
        # Require model information, not just brand
        # iPhone alone is NOT valid - needs model number like "iPhone 14"
        if not has_model_info:
            return False, (
                f"Please include the mobile model name (e.g., 'Samsung Galaxy S23', 'iPhone 14 Pro', 'Redmi Note 12'). "
                f"Just the brand name '{detected_brand.title() if detected_brand else found_brands[0]}' is not enough."
            ), extracted
        
        # Valid if brand found, model info present, and no conflicts detected
        return True, "", extracted
    
    @classmethod
    def validate_laptop_title(cls, title: str, description: str = "") -> Tuple[bool, str, Dict]:
        """
        Validate laptop title contains brand information and check brand-model consistency
        Comprehensively validates that brand and model combinations are valid (e.g., no "HP MacBook")
        
        Returns:
            (is_valid, error_message, extracted_info)
        """
        text = f"{title} {description}".lower()
        
        # Check for any laptop brand keyword
        found_brands = [brand for brand in cls.LAPTOP_BRANDS if brand in text]
        
        if not found_brands:
            return False, (
                "Laptop title must include a brand name (e.g., Dell, HP, Lenovo, Apple MacBook, etc.)."
            ), {}
        
        # Comprehensive brand-model conflict detection for laptops
        detected_brand = None
        conflicting_models = []
        
        # Determine primary brand
        for brand_key, exclusive_keywords in cls.LAPTOP_BRAND_EXCLUSIVE.items():
            # Check if this brand is mentioned
            brand_mentioned = brand_key in text
            if brand_key == 'dell':
                brand_mentioned = 'dell' in text or 'alienware' in text
            elif brand_key == 'lenovo':
                brand_mentioned = 'lenovo' in text or 'thinkpad' in text or 'ideapad' in text
            elif brand_key == 'hp':
                brand_mentioned = 'hp' in text or 'pavilion' in text or 'envy' in text or 'elitebook' in text or 'probook' in text
            elif brand_key == 'apple':
                brand_mentioned = 'apple' in text or 'macbook' in text
            elif brand_key == 'asus':
                brand_mentioned = 'asus' in text or 'vivobook' in text or 'zenbook' in text
            elif brand_key == 'acer':
                brand_mentioned = 'acer' in text or 'predator' in text or 'nitro' in text
            elif brand_key == 'microsoft':
                brand_mentioned = 'microsoft' in text or 'surface' in text
                
            if brand_mentioned:
                detected_brand = brand_key
                break
        
        # If we detected a primary brand, check for conflicting models from other brands
        if detected_brand:
            for other_brand, other_keywords in cls.LAPTOP_BRAND_EXCLUSIVE.items():
                if other_brand != detected_brand:
                    # Check if any exclusive keywords from other brands appear
                    conflicts = [kw for kw in other_keywords if kw in text and len(kw) > 3]
                    
                    # Filter out common generic terms
                    generic_terms = {'gaming', 'chromebook', 'notebook'}
                    significant_conflicts = [c for c in conflicts if c not in generic_terms]
                    
                    if significant_conflicts:
                        conflicting_models.extend([(other_brand, c) for c in significant_conflicts])
        
        # Report conflicts if found
        if conflicting_models:
            conflict_brand, conflict_model = conflicting_models[0]
            return False, (
                f"Invalid brand-model combination: '{detected_brand.title()}' cannot have '{conflict_model}' "
                f"(which is exclusive to {conflict_brand.title()}). "
                f"Example: HP cannot have MacBook, Dell cannot have ThinkPad. "
                f"Please use correct brand and model name."
            ), {}
        
        # Extract optional information (not required)
        found_processors = [proc for proc in cls.LAPTOP_PROCESSORS if proc in text]
        
        extracted = {
            'brands': found_brands,
            'detected_brand': detected_brand,
            'processors': found_processors,
            'has_generation': bool(re.search(r'\d+(th|st|nd|rd)?\s*gen', text)),
            'has_ram': bool(re.search(r'\d+\s*gb\s*(ram|ddr)', text)),
            'has_storage': bool(re.search(r'\d+\s*(gb|tb)\s*(ssd|hdd|nvme|storage)', text))
        }
        
        # Check for model/series information - require more than just brand name
        has_model_info = False
        
        # Check for model series names from brand-exclusive keywords
        for brand_key, exclusive_keywords in cls.LAPTOP_BRAND_EXCLUSIVE.items():
            for keyword in exclusive_keywords:
                if keyword in text:
                    has_model_info = True
                    break
            if has_model_info:
                break
        
        # Check for processor info (i5, i7, Ryzen, M1, etc.)
        if found_processors:
            has_model_info = True
        
        # Check for generation info
        if re.search(r'\d+(th|st|nd|rd)?\s*gen', text):
            has_model_info = True
        
        # Check for common laptop model indicators
        laptop_model_keywords = {
            'inspiron', 'latitude', 'precision', 'xps', 'vostro', 'alienware',
            'pavilion', 'envy', 'elitebook', 'probook', 'omen', 'spectre', 'victus', 'zbook',
            'thinkpad', 'ideapad', 'yoga', 'legion', 'thinkbook',
            'macbook', 'macbook pro', 'macbook air',
            'vivobook', 'zenbook', 'rog', 'tuf', 'expertbook',
            'aspire', 'predator', 'nitro', 'swift', 'spin', 'travelmate',
            'katana', 'blade', 'surface', 'gram', 'gaming'
        }
        
        for keyword in laptop_model_keywords:
            if keyword in text:
                has_model_info = True
                break
        
        extracted['has_model_info'] = has_model_info
        
        # Check for explicit brand name (Dell, HP, Lenovo, etc.) - not just model keywords
        explicit_brands = {'dell', 'hp', 'lenovo', 'asus', 'acer', 'apple', 'msi', 'razer', 'microsoft', 'samsung', 'lg'}
        has_explicit_brand = any(brand in text for brand in explicit_brands)
        
        # For MacBook, check for 'macbook' or 'apple'
        if 'macbook' in text:
            has_explicit_brand = True
        
        # Require explicit brand name
        if not has_explicit_brand:
            return False, (
                f"Please include the laptop brand name (e.g., 'Dell', 'HP', 'Lenovo', 'ASUS', 'Apple MacBook'). "
                f"Just model keywords like 'Inspiron' or 'ThinkPad' are not enough."
            ), extracted
        
        # Require model information, not just brand
        if not has_model_info:
            return False, (
                f"Please include the laptop model/series (e.g., 'Dell Inspiron i5', 'HP Pavilion', 'MacBook Air M1'). "
                f"Just the brand name '{detected_brand.title() if detected_brand else found_brands[0]}' is not enough."
            ), extracted
        
        # Valid if brand found, model info present, and no conflicts detected
        return True, "", extracted
    
    @classmethod
    def validate_furniture_title(cls, title: str, description: str = "", material: str = "") -> Tuple[bool, str, Dict]:
        """
        Validate furniture title contains type information and is strictly furniture-related
        Rejects listings that contain electronics or non-furniture keywords
        
        Returns:
            (is_valid, error_message, extracted_info)
        """
        text = f"{title} {description} {material}".lower()
        
        # First, check for non-furniture keywords (electronics, phones, laptops, etc.)
        found_non_furniture = [kw for kw in cls.NON_FURNITURE_KEYWORDS if kw in text]
        
        if found_non_furniture:
            return False, (
                f"This appears to be a {found_non_furniture[0]} listing, not furniture. "
                "Furniture category is for items like sofas, chairs, tables, beds, etc. "
                f"Please select the correct category for '{found_non_furniture[0]}'."
            ), {}
        
        # Check for any furniture type keyword
        found_types = [ftype for ftype in cls.FURNITURE_TYPES if ftype in text]
        
        if not found_types:
            return False, (
                "Furniture title must include the type of furniture (e.g., Sofa, Chair, Table, Bed, etc.). "
                "Please specify what type of furniture item this is."
            ), {}
        
        # Check for material (optional)
        found_materials = [mat for mat in cls.FURNITURE_MATERIALS if mat in text]
        
        extracted = {
            'types': found_types,
            'materials': found_materials,
            'has_dimensions': bool(re.search(r'\d+\s*(cm|inch|ft|meter)', text)),
            'has_seating': bool(re.search(r'\d+\s*seater', text))
        }
        
        # Valid if furniture type found and no electronics keywords detected
        return True, "", extracted
    
    @classmethod
    def validate_title(cls, category: str, title: str, description: str = "", **kwargs) -> Tuple[bool, str, Dict]:
        """
        Main validation method that routes to category-specific validators
        
        Args:
            category: 'mobile', 'laptop', or 'furniture'
            title: Product title
            description: Product description (optional)
            **kwargs: Additional category-specific fields (e.g., material for furniture)
        
        Returns:
            (is_valid, error_message, extracted_info)
        """
        category = category.lower().strip()
        
        if category == 'mobile':
            return cls.validate_mobile_title(title, description)
        elif category == 'laptop':
            return cls.validate_laptop_title(title, description)
        elif category == 'furniture':
            material = kwargs.get('material', '')
            return cls.validate_furniture_title(title, description, material)
        else:
            return False, f"Invalid category: {category}. Must be 'mobile', 'laptop', or 'furniture'.", {}
    
    @classmethod
    def get_validation_hints(cls, category: str) -> Dict[str, List[str]]:
        """Get helpful hints for creating valid titles"""
        
        if category == 'mobile':
            return {
                'required': ['Brand name (e.g., Samsung, iPhone, Xiaomi)'],
                'recommended': ['Model number/name (e.g., S23, 14 Pro)', 'RAM and storage', 'Condition'],
                'example': 'Samsung Galaxy S23 Ultra 12GB RAM 256GB Storage - Excellent Condition'
            }
        
        elif category == 'laptop':
            return {
                'required': ['Brand name (e.g., Dell, HP, Lenovo)', 'Processor or generation (e.g., i7 12th Gen)'],
                'recommended': ['RAM (e.g., 16GB)', 'Storage (e.g., 512GB SSD)', 'Model name'],
                'example': 'Dell XPS 15 Intel Core i7 12th Gen 16GB RAM 512GB SSD'
            }
        
        elif category == 'furniture':
            return {
                'required': ['Furniture type (e.g., Sofa, Chair, Table)', 'Material (e.g., Wood, Leather)'],
                'recommended': ['Dimensions', 'Seating capacity', 'Style (modern, antique)'],
                'example': 'Modern 5 Seater L-Shape Sofa - Premium Fabric with Wooden Frame'
            }
        
        return {}
    
    @classmethod
    def extract_keywords(cls, category: str, text: str) -> Dict[str, List[str]]:
        """Extract relevant keywords from text based on category"""
        
        text_lower = text.lower()
        keywords = {}
        
        if category == 'mobile':
            keywords['brands'] = [b for b in cls.MOBILE_BRANDS if b in text_lower]
            
        elif category == 'laptop':
            keywords['brands'] = [b for b in cls.LAPTOP_BRANDS if b in text_lower]
            keywords['processors'] = [p for p in cls.LAPTOP_PROCESSORS if p in text_lower]
            
        elif category == 'furniture':
            keywords['types'] = [t for t in cls.FURNITURE_TYPES if t in text_lower]
            keywords['materials'] = [m for m in cls.FURNITURE_MATERIALS if m in text_lower]
        
        return keywords
