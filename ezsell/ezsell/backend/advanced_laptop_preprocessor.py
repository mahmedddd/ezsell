"""
Advanced Laptop Preprocessor - Improved Feature Extraction & Engineering
Target: 75%+ R² through better features and domain knowledge
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple

class AdvancedLaptopPreprocessor:
    """Enhanced preprocessor with superior feature extraction"""
    
    def __init__(self):
        # Brand reputation scores (based on market positioning)
        self.brand_scores = {
            'dell': 8, 'hp': 8, 'lenovo': 8, 'asus': 7, 'acer': 6,
            'msi': 9, 'razer': 10, 'alienware': 10, 'macbook': 10, 'apple': 10,
            'microsoft': 9, 'surface': 9, 'thinkpad': 9, 'latitude': 8,
            'elitebook': 9, 'probook': 7, 'inspiron': 6, 'pavilion': 6,
            'toshiba': 5, 'samsung': 7, 'huawei': 7, 'lg': 6
        }
        
        # Premium model keywords
        self.premium_models = [
            'xps', 'spectre', 'envy', 'thinkpad', 'latitude', 'elitebook',
            'zbook', 'macbook', 'surface', 'alienware', 'razer', 'rog', 'tuf'
        ]
        
        # Gaming indicators
        self.gaming_keywords = [
            'gaming', 'rog', 'tuf', 'predator', 'legion', 'omen', 
            'alienware', 'razer', 'msi', 'rtx', 'gtx', 'nitro'
        ]
    
    def extract_brand(self, text: str) -> Tuple[str, int]:
        """Extract brand and reputation score"""
        text_lower = text.lower()
        
        for brand, score in sorted(self.brand_scores.items(), key=lambda x: len(x[0]), reverse=True):
            if brand in text_lower:
                return brand, score
        
        return 'unknown', 3
    
    def extract_ram_improved(self, text: str) -> int:
        """Improved RAM extraction with multiple patterns"""
        text_lower = text.lower()
        
        # Pattern 1: "8gb ram" or "8 gb ram"
        match = re.search(r'(\d+)\s*gb\s+ram', text_lower)
        if match:
            ram = int(match.group(1))
            if 2 <= ram <= 128:
                return ram
        
        # Pattern 2: "ram 8gb" or "ram: 8gb"
        match = re.search(r'ram[\s:]+(\d+)\s*gb', text_lower)
        if match:
            ram = int(match.group(1))
            if 2 <= ram <= 128:
                return ram
        
        # Pattern 3: Just "8gb" near start (likely RAM)
        match = re.search(r'\b(\d+)\s*gb\b', text_lower[:200])
        if match:
            ram = int(match.group(1))
            if ram in [2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64, 128]:
                return ram
        
        # Pattern 4: "memory 8gb"
        match = re.search(r'memory[\s:]+(\d+)\s*gb', text_lower)
        if match:
            ram = int(match.group(1))
            if 2 <= ram <= 128:
                return ram
        
        return None
    
    def extract_storage_improved(self, text: str) -> Tuple[int, str, int]:
        """Improved storage extraction - returns (size_gb, type, score)"""
        text_lower = text.lower()
        
        storage_gb = None
        storage_type = 'unknown'
        
        # Pattern 1: "512gb ssd" or "1tb ssd"
        match = re.search(r'(\d+)\s*(tb|gb)\s+(ssd|hdd|nvme|m\.?2)', text_lower)
        if match:
            size, unit, stype = match.groups()
            storage_gb = int(size) * (1024 if unit == 'tb' else 1)
            storage_type = stype
        
        # Pattern 2: "ssd 512gb" or "ssd: 512gb"
        if not storage_gb:
            match = re.search(r'(ssd|hdd|nvme|m\.?2)[\s:]+(\d+)\s*(tb|gb)', text_lower)
            if match:
                stype, size, unit = match.groups()
                storage_gb = int(size) * (1024 if unit == 'tb' else 1)
                storage_type = stype
        
        # Pattern 3: "storage 512gb"
        if not storage_gb:
            match = re.search(r'storage[\s:]+(\d+)\s*(tb|gb)', text_lower)
            if match:
                size, unit = match.groups()
                storage_gb = int(size) * (1024 if unit == 'tb' else 1)
        
        # Pattern 4: Look for just TB/GB mentions (likely storage)
        if not storage_gb:
            match = re.search(r'(\d+)\s*(tb|gb)(?!\s*ram)', text_lower)
            if match:
                size, unit = match.groups()
                size_val = int(size) * (1024 if unit == 'tb' else 1)
                # Validate it's storage range (128GB - 8TB)
                if 128 <= size_val <= 8192:
                    storage_gb = size_val
        
        # Detect type if not found
        if storage_gb and storage_type == 'unknown':
            if 'ssd' in text_lower or 'nvme' in text_lower or 'm.2' in text_lower or 'm2' in text_lower:
                storage_type = 'ssd'
            elif 'hdd' in text_lower:
                storage_type = 'hdd'
            else:
                storage_type = 'ssd'  # Default to SSD for modern laptops
        
        # Calculate storage score
        storage_score = 0
        if storage_gb:
            storage_score = storage_gb
            if storage_type in ['ssd', 'nvme', 'm.2', 'm2']:
                storage_score += 200  # SSD premium
        
        return storage_gb, storage_type, storage_score
    
    def extract_processor_improved(self, text: str) -> Dict:
        """Enhanced processor extraction"""
        text_lower = text.lower()
        
        result = {
            'tier': 0,
            'brand': 0,  # 0=unknown, 1=Intel, 2=AMD, 3=Apple
            'generation': 0,
            'model': '',
            'score': 0
        }
        
        # Intel processors
        intel_match = re.search(r'(?:core\s+)?(i[3579])(?:\s+|-)(\d{4}|(\d+)(?:th|st|nd|rd)?\s*gen)', text_lower)
        if intel_match:
            tier_str = intel_match.group(1)
            gen_str = intel_match.group(2)
            
            tier_map = {'i3': 1, 'i5': 2, 'i7': 3, 'i9': 4}
            result['tier'] = tier_map.get(tier_str, 0)
            result['brand'] = 1
            result['model'] = f"Intel {tier_str}"
            
            # Extract generation
            gen_match = re.search(r'(\d+)', gen_str)
            if gen_match:
                gen = int(gen_match.group(1))
                if gen > 100:  # Like 1235U (12th gen)
                    gen = int(str(gen)[:2])
                result['generation'] = min(gen, 14)
        
        # AMD Ryzen
        amd_match = re.search(r'ryzen\s+([3579])(?:\s+(\d{4})|\s+(\d+)(?:th|st|nd|rd)?\s*gen)?', text_lower)
        if amd_match and not intel_match:  # Prefer Intel if both found
            tier_str = amd_match.group(1)
            tier_map = {'3': 1, '5': 2, '7': 3, '9': 4}
            result['tier'] = tier_map.get(tier_str, 0)
            result['brand'] = 2
            result['model'] = f"Ryzen {tier_str}"
            
            if amd_match.group(2):
                model_num = int(amd_match.group(2))
                gen = int(str(model_num)[0])
                result['generation'] = min(gen, 8)
        
        # Calculate processor score
        result['score'] = (result['tier'] * 25) + (result['generation'] * 3) + (result['brand'] * 5)
        
        return result
    
    def extract_gpu_improved(self, text: str) -> Dict:
        """Enhanced GPU extraction"""
        text_lower = text.lower()
        
        result = {
            'tier': 0,
            'has_dedicated': 0,
            'is_gaming': 0,
            'vram': None,
            'score': 0
        }
        
        # NVIDIA RTX
        rtx_match = re.search(r'rtx\s*(\d{4})', text_lower)
        if rtx_match:
            model = int(rtx_match.group(1))
            result['has_dedicated'] = 1
            result['is_gaming'] = 1
            
            # RTX 40 series
            if model >= 4050:
                result['tier'] = 10
            # RTX 30 series
            elif model >= 3050:
                result['tier'] = 8
            # RTX 20 series
            elif model >= 2060:
                result['tier'] = 6
        
        # NVIDIA GTX
        gtx_match = re.search(r'gtx\s*(\d{4})', text_lower)
        if gtx_match and not rtx_match:
            model = int(gtx_match.group(1))
            result['has_dedicated'] = 1
            result['is_gaming'] = 1
            
            if model >= 1650:
                result['tier'] = 5
            elif model >= 1050:
                result['tier'] = 4
        
        # AMD Radeon
        rx_match = re.search(r'(?:radeon\s+)?rx\s*(\d{4})', text_lower)
        if rx_match and not rtx_match and not gtx_match:
            model = int(rx_match.group(1))
            result['has_dedicated'] = 1
            
            if model >= 6000:
                result['tier'] = 7
            elif model >= 5000:
                result['tier'] = 5
        
        # Integrated graphics
        if 'intel uhd' in text_lower or 'intel iris' in text_lower:
            result['tier'] = 1
        elif 'vega' in text_lower or 'radeon graphics' in text_lower:
            result['tier'] = 2
        
        # VRAM detection
        vram_match = re.search(r'(\d+)\s*gb\s+(?:vram|gddr|graphics)', text_lower)
        if vram_match:
            result['vram'] = int(vram_match.group(1))
        
        # Calculate GPU score
        result['score'] = (result['tier'] * 15) + (result['has_dedicated'] * 30) + ((result['vram'] or 0) * 5)
        
        return result
    
    def extract_display_features(self, text: str) -> Dict:
        """Extract display specifications"""
        text_lower = text.lower()
        
        return {
            'screen_size': self._extract_screen_size(text_lower),
            'is_fullhd': 1 if any(k in text_lower for k in ['full hd', '1080p', 'fhd', '1920']) else 0,
            'is_2k': 1 if any(k in text_lower for k in ['2k', '1440p', '2560']) else 0,
            'is_4k': 1 if any(k in text_lower for k in ['4k', 'uhd', '3840']) else 0,
            'is_touchscreen': 1 if 'touch' in text_lower else 0,
            'refresh_rate': self._extract_refresh_rate(text_lower)
        }
    
    def _extract_screen_size(self, text: str) -> float:
        """Extract screen size in inches"""
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:inch|"|\'\')', text)
        if match:
            size = float(match.group(1))
            if 10 <= size <= 18:
                return size
        
        # Common sizes
        for size in [13.3, 14, 15.6, 17.3]:
            if str(size).replace('.', '') in text:
                return size
        
        return 15.6  # Default
    
    def _extract_refresh_rate(self, text: str) -> int:
        """Extract refresh rate in Hz"""
        match = re.search(r'(\d+)\s*hz', text)
        if match:
            hz = int(match.group(1))
            if hz in [60, 90, 120, 144, 165, 240]:
                return hz
        return 60  # Default
    
    def extract_condition_features(self, text: str, condition: str) -> Dict:
        """Extract condition and age features"""
        text_lower = text.lower()
        
        # Determine condition score
        condition_lower = str(condition).lower()
        if 'new' in condition_lower or 'brand new' in text_lower:
            condition_score = 10
            is_new = 1
            is_used = 0
        elif 'like new' in condition_lower or 'excellent' in condition_lower:
            condition_score = 9
            is_new = 0
            is_used = 1
        elif 'good' in condition_lower:
            condition_score = 7
            is_new = 0
            is_used = 1
        else:
            condition_score = 5
            is_new = 0
            is_used = 1
        
        # Warranty detection
        has_warranty = 1 if any(k in text_lower for k in ['warrant', 'guarantee']) else 0
        
        # Age estimation from year
        current_year = 2024
        year_match = re.search(r'20(\d{2})', text_lower)
        age_years = 0
        if year_match:
            year = 2000 + int(year_match.group(1))
            if 2015 <= year <= 2024:
                age_years = current_year - year
        
        return {
            'condition_score': condition_score,
            'is_new': is_new,
            'is_used': is_used,
            'has_warranty': has_warranty,
            'age_years': age_years,
            'age_penalty': age_years * -5  # Older = cheaper
        }
    
    def extract_special_features(self, text: str) -> Dict:
        """Extract special features and keywords"""
        text_lower = text.lower()
        
        return {
            'is_gaming': 1 if any(k in text_lower for k in self.gaming_keywords) else 0,
            'is_2in1': 1 if any(k in text_lower for k in ['2 in 1', '2-in-1', 'convertible', 'detachable']) else 0,
            'is_premium': 1 if any(k in text_lower for k in self.premium_models) else 0,
            'has_backlit': 1 if 'backlit' in text_lower or 'backlight' in text_lower else 0,
            'has_fingerprint': 1 if 'fingerprint' in text_lower else 0,
            'has_webcam': 1 if 'webcam' in text_lower or 'camera' in text_lower else 0,
            'battery_wh': self._extract_battery(text_lower),
            'weight_kg': self._extract_weight(text_lower)
        }
    
    def _extract_battery(self, text: str) -> int:
        """Extract battery capacity"""
        match = re.search(r'(\d+)\s*wh', text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_weight(self, text: str) -> float:
        """Extract weight in kg"""
        match = re.search(r'(\d+(?:\.\d+)?)\s*kg', text)
        if match:
            return float(match.group(1))
        return None
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main preprocessing pipeline"""
        print("\n=== Advanced Laptop Preprocessing ===\n")
        print(f"Initial records: {len(df)}")
        
        # Initialize feature columns
        features = []
        
        for idx, row in df.iterrows():
            text = str(row.get('Description', '')) + ' ' + str(row.get('Title', ''))
            condition = row.get('Condition', 'Used')
            
            feat = {}
            
            # Brand features
            brand, brand_score = self.extract_brand(text)
            feat['brand'] = brand
            feat['brand_score'] = brand_score
            
            # RAM (improved)
            feat['ram'] = self.extract_ram_improved(text)
            
            # Storage (improved)
            storage_gb, storage_type, storage_score = self.extract_storage_improved(text)
            feat['storage_gb'] = storage_gb
            feat['storage_type'] = storage_type
            feat['storage_score'] = storage_score
            feat['is_ssd'] = 1 if storage_type in ['ssd', 'nvme', 'm.2', 'm2'] else 0
            
            # Processor (improved)
            proc = self.extract_processor_improved(text)
            feat['processor_tier'] = proc['tier']
            feat['processor_brand'] = proc['brand']
            feat['processor_generation'] = proc['generation']
            feat['processor_model'] = proc['model']
            feat['processor_score'] = proc['score']
            
            # GPU (improved)
            gpu = self.extract_gpu_improved(text)
            feat['gpu_tier'] = gpu['tier']
            feat['has_dedicated_gpu'] = gpu['has_dedicated']
            feat['is_gaming_gpu'] = gpu['is_gaming']
            feat['gpu_vram'] = gpu['vram']
            feat['gpu_score'] = gpu['score']
            
            # Display
            display = self.extract_display_features(text)
            feat.update(display)
            
            # Condition
            cond = self.extract_condition_features(text, condition)
            feat.update(cond)
            
            # Special features
            special = self.extract_special_features(text)
            feat.update(special)
            
            # Text features
            feat['text_length'] = len(text)
            feat['word_count'] = len(text.split())
            
            # Composite scores
            feat['total_specs_score'] = (
                feat['processor_score'] + 
                feat['storage_score'] + 
                feat['gpu_score'] + 
                (feat['ram'] or 0) * 10 +
                feat['condition_score'] * 5
            )
            
            feat['price'] = row['Price']
            features.append(feat)
        
        result_df = pd.DataFrame(features)
        
        # Feature completeness report
        print("\n=== Feature Extraction Success Rates ===")
        key_features = ['ram', 'storage_gb', 'processor_tier', 'gpu_tier', 'brand']
        for feat in key_features:
            if feat in result_df.columns:
                non_null = result_df[feat].notna().sum()
                pct = non_null / len(result_df) * 100
                print(f"  {feat:20s}: {non_null:4d}/{len(result_df)} ({pct:5.1f}%)")
        
        return result_df

if __name__ == '__main__':
    # Load dataset
    df = pd.read_csv('laptop_scraped_20251221_051440.csv')
    
    # Filter Featured only
    df = df[df['Title'] == 'Featured'].copy()
    
    # Remove placeholder prices
    df = df[df['Price'] >= 5000].copy()
    
    print(f"\nProcessing {len(df)} laptops...")
    
    # Preprocess
    preprocessor = AdvancedLaptopPreprocessor()
    processed_df = preprocessor.preprocess(df)
    
    # Save
    output_file = 'scraped_data/laptop_advanced_clean.csv'
    processed_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Saved {len(processed_df)} records to {output_file}")
    print(f"\nPrice stats:")
    print(f"  Mean: Rs.{processed_df['price'].mean():,.0f}")
    print(f"  Median: Rs.{processed_df['price'].median():,.0f}")
    print(f"  Range: Rs.{processed_df['price'].min():,.0f} - Rs.{processed_df['price'].max():,.0f}")
