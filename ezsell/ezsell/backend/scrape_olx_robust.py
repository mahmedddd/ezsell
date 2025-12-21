"""
Robust OLX Pakistan Scraper with NLP Extraction
Extracts detailed specs from titles and descriptions for accurate price prediction
"""

import time
import re
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import random
import undetected_chromedriver as uc

class NLPExtractor:
    """NLP-based feature extraction from text"""
    
    # Mobile keywords and patterns
    MOBILE_RAM_PATTERNS = [
        r'(\d+)\s*gb[\s/]+(\d+)\s*gb',  # 8GB/128GB or 8/128
        r'(\d+)/(\d+)',  # 8/256
        r'(\d+)\s*gb\s*ram'  # 8GB RAM
    ]
    
    MOBILE_STORAGE_PATTERNS = [
        r'/\s*(\d+)\s*gb',  # /128GB
        r'(\d{2,4})\s*gb(?!\s*ram)',  # 128GB (not RAM)
    ]
    
    MOBILE_CONDITIONS = {
        'new': ['new', 'brand new', 'sealed', 'unused', '10/10', 'mint'],
        'excellent': ['excellent', '9.5/10', '9/10', 'like new', 'barely used'],
        'good': ['good', '8/10', '8.5/10', 'working', 'good condition'],
        'fair': ['fair', '7/10', '6/10', 'minor scratches', 'some wear'],
        'used': ['used', 'old', 'average']
    }
    
    MOBILE_FEATURES = {
        '5g': r'\b5g\b',
        'pta_approved': r'\bpta\b',
        'amoled': r'\bamoled\b|\bsuper amoled\b',
        'warranty': r'\bwarranty\b',
        'box': r'\bbox\b|\boriginal box\b',
        'charger': r'\bcharger\b',
        'dual_sim': r'\bdual sim\b',
        'fingerprint': r'\bfingerprint\b|\btouch id\b|\bface id\b',
        'waterproof': r'\bwater\s*proof\b|\bip\d+\b'
    }
    
    # Laptop keywords and patterns
    LAPTOP_PROCESSOR_PATTERNS = {
        'i9': (r'\bi9\b', 9),
        'i7': (r'\bi7\b', 7),
        'i5': (r'\bi5\b', 5),
        'i3': (r'\bi3\b', 3),
        'ryzen 9': (r'\bryzen\s*9\b', 9),
        'ryzen 7': (r'\bryzen\s*7\b', 8),
        'ryzen 5': (r'\bryzen\s*5\b', 6),
        'ryzen 3': (r'\bryzen\s*3\b', 4),
        'm1': (r'\bm1\b', 10),
        'm2': (r'\bm2\b', 10),
        'm3': (r'\bm3\b', 10),
        'celeron': (r'\bceleron\b', 2),
        'pentium': (r'\bpentium\b', 2)
    }
    
    LAPTOP_GPU_PATTERNS = {
        'rtx 4090': (r'\brtx\s*4090\b', 10),
        'rtx 4080': (r'\brtx\s*4080\b', 9),
        'rtx 4070': (r'\brtx\s*4070\b', 9),
        'rtx 4060': (r'\brtx\s*4060\b', 8),
        'rtx 3080': (r'\brtx\s*3080\b', 8),
        'rtx 3070': (r'\brtx\s*3070\b', 8),
        'rtx 3060': (r'\brtx\s*3060\b', 7),
        'rtx 3050': (r'\brtx\s*3050\b', 6),
        'gtx 1650': (r'\bgtx\s*1650\b', 5),
        'mx': (r'\bmx\s*\d+\b', 3),
        'integrated': (r'\bintegrated\b|\buhd\b', 1)
    }
    
    LAPTOP_FEATURES = {
        'gaming': r'\bgaming\b|\brog\b|\btuf\b|\balienware\b|\bpredator\b',
        'touchscreen': r'\btouch\s*screen\b|\btouch\b',
        'ssd': r'\bssd\b',
        'backlit': r'\bbacklit\b|\brgb\b',
        'webcam': r'\bwebcam\b',
        'fingerprint': r'\bfingerprint\b',
        'convertible': r'\bconvertible\b|\b2\s*in\s*1\b'
    }
    
    LAPTOP_CONDITIONS = {
        'new': ['new', 'brand new', 'sealed', 'unused', '10/10'],
        'excellent': ['excellent', '9/10', 'like new', 'mint'],
        'good': ['good', '8/10', 'working perfectly'],
        'fair': ['fair', '7/10', 'minor issues'],
        'used': ['used', 'working']
    }
    
    # Furniture keywords and patterns
    FURNITURE_MATERIALS = {
        'solid wood': (r'\bsolid\s*wood\b|\bsheesham\b|\bteak\b|\boak\b', 9),
        'wood': (r'\bwood\b|\bwooden\b', 7),
        'metal': (r'\bmetal\b|\bsteel\b|\biron\b', 6),
        'leather': (r'\bleather\b|\bgenuine\s*leather\b', 8),
        'fabric': (r'\bfabric\b|\bvelvet\b|\bcloth\b', 5),
        'plastic': (r'\bplastic\b', 3),
        'glass': (r'\bglass\b', 4),
        'mdf': (r'\bmdf\b|\bparticle\s*board\b', 4),
        'marble': (r'\bmarble\b', 7),
        'rexine': (r'\brexine\b', 4)
    }
    
    FURNITURE_CONDITIONS = {
        'new': ['new', 'brand new', 'unused', '10/10'],
        'excellent': ['excellent', '9/10', 'like new', 'mint'],
        'good': ['good', '8/10', 'working'],
        'fair': ['fair', '7/10', 'some scratches'],
        'used': ['used', 'old']
    }
    
    FURNITURE_FEATURES = {
        'imported': r'\bimport\w*\b',
        'handmade': r'\bhand\s*made\b|\bhandmade\b',
        'storage': r'\bstorage\b',
        'modern': r'\bmodern\b|\bcontemporary\b',
        'antique': r'\bantique\b|\bvintage\b|\bclassic\b',
        'cushioned': r'\bcushion\w*\b',
        'adjustable': r'\badjustable\b',
        'foldable': r'\bfoldable\b|\bfolding\b'
    }
    
    @staticmethod
    def extract_mobile_features(title, description):
        """Extract mobile phone features"""
        text = f"{title} {description}".lower()
        features = {}
        
        # RAM and Storage
        ram_found = False
        for pattern in NLPExtractor.MOBILE_RAM_PATTERNS:
            match = re.search(pattern, text)
            if match:
                features['ram'] = int(match.group(1))
                if len(match.groups()) > 1:
                    features['storage'] = int(match.group(2))
                ram_found = True
                break
        
        if not ram_found:
            # Try RAM only
            ram_match = re.search(r'(\d+)\s*gb\s*ram', text)
            features['ram'] = int(ram_match.group(1)) if ram_match else None
        
        if 'storage' not in features:
            # Try storage separately
            for pattern in NLPExtractor.MOBILE_STORAGE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    features['storage'] = int(match.group(1))
                    break
        
        # Camera
        camera_match = re.search(r'(\d+)\s*mp', text)
        features['camera_mp'] = int(camera_match.group(1)) if camera_match else None
        
        # Battery
        battery_match = re.search(r'(\d{4,5})\s*mah', text)
        features['battery_mah'] = int(battery_match.group(1)) if battery_match else None
        
        # Screen size
        screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', text)
        features['screen_size'] = float(screen_match.group(1)) if screen_match else None
        
        # Boolean features
        for feature, pattern in NLPExtractor.MOBILE_FEATURES.items():
            features[feature] = 1 if re.search(pattern, text) else 0
        
        # Condition
        features['condition'] = NLPExtractor.extract_condition(text, NLPExtractor.MOBILE_CONDITIONS)
        
        return features
    
    @staticmethod
    def extract_laptop_features(title, description):
        """Extract laptop features"""
        text = f"{title} {description}".lower()
        features = {}
        
        # Processor
        features['processor_tier'] = 5  # Default
        for name, (pattern, tier) in NLPExtractor.LAPTOP_PROCESSOR_PATTERNS.items():
            if re.search(pattern, text):
                features['processor_tier'] = tier
                features['processor_name'] = name
                break
        
        # Generation
        gen_match = re.search(r'(\d+)(?:th|nd|rd|st)?\s*gen', text)
        features['generation'] = int(gen_match.group(1)) if gen_match else None
        
        # RAM
        ram_match = re.search(r'(\d+)\s*gb\s*ram', text)
        features['ram'] = int(ram_match.group(1)) if ram_match else None
        
        # Storage
        storage_match = re.search(r'(\d{3,4})\s*gb\s*(?:ssd|hdd|storage)', text)
        if not storage_match:
            storage_match = re.search(r'(\d{3,4})\s*gb', text)
        features['storage'] = int(storage_match.group(1)) if storage_match else None
        
        # GPU
        features['gpu_tier'] = 0
        for name, (pattern, tier) in NLPExtractor.LAPTOP_GPU_PATTERNS.items():
            if re.search(pattern, text):
                features['gpu_tier'] = tier
                features['gpu_name'] = name
                break
        
        # Screen size
        screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|\')', text)
        features['screen_size'] = float(screen_match.group(1)) if screen_match else None
        
        # Boolean features
        for feature, pattern in NLPExtractor.LAPTOP_FEATURES.items():
            features[feature] = 1 if re.search(pattern, text) else 0
        
        # Condition
        features['condition'] = NLPExtractor.extract_condition(text, NLPExtractor.LAPTOP_CONDITIONS)
        
        return features
    
    @staticmethod
    def extract_furniture_features(title, description):
        """Extract furniture features"""
        text = f"{title} {description}".lower()
        features = {}
        
        # Material
        features['material_score'] = 5  # Default
        features['material'] = 'Other'
        for material, (pattern, score) in NLPExtractor.FURNITURE_MATERIALS.items():
            if re.search(pattern, text):
                features['material_score'] = score
                features['material'] = material.title()
                break
        
        # Seating capacity
        seating_match = re.search(r'(\d+)\s*seater', text)
        features['seating_capacity'] = int(seating_match.group(1)) if seating_match else None
        
        # Dimensions (LxWxH)
        dim_match = re.search(r'(\d+)\s*(?:x|×)\s*(\d+)\s*(?:x|×)\s*(\d+)', text)
        if dim_match:
            features['length'] = int(dim_match.group(1))
            features['width'] = int(dim_match.group(2))
            features['height'] = int(dim_match.group(3))
        else:
            features['length'] = None
            features['width'] = None
            features['height'] = None
        
        # Boolean features
        for feature, pattern in NLPExtractor.FURNITURE_FEATURES.items():
            features[feature] = 1 if re.search(pattern, text) else 0
        
        # Condition
        features['condition'] = NLPExtractor.extract_condition(text, NLPExtractor.FURNITURE_CONDITIONS)
        
        return features
    
    @staticmethod
    def extract_condition(text, condition_dict):
        """Extract condition from text"""
        for condition, keywords in condition_dict.items():
            if any(keyword in text for keyword in keywords):
                return condition.title()
        return 'Used'


class OLXScraper:
    """Base scraper for OLX Pakistan"""
    
    def __init__(self, headless=False):
        self.setup_driver(headless)
        self.base_url = "https://www.olx.com.pk"
        self.data = []
        
    def setup_driver(self, headless):
        """Setup undetected Chrome driver"""
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to avoid detection"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def extract_price_from_text(self, text):
        """Extract price from text"""
        match = re.search(r'Rs[\s]*([0-9,]+)', text)
        if match:
            price_str = match.group(1).replace(',', '')
            return int(price_str)
        return None
    
    def close(self):
        """Close driver"""
        self.driver.quit()


class MobileScraper(OLXScraper):
    """Scraper for mobile phones"""
    
    def __init__(self, target_count=5000, headless=False):
        super().__init__(headless)
        self.target_count = target_count
        self.category_url = f"{self.base_url}/mobile-phones_c1453"
        self.brands = ['apple', 'samsung', 'xiaomi', 'oppo', 'vivo', 'infinix', 
                       'tecno', 'realme', 'oneplus', 'huawei', 'nokia', 'motorola']
        
    def scrape(self):
        """Scrape mobile listings"""
        print(f"\n{'='*80}")
        print(f"📱 SCRAPING MOBILE PHONES - Target: {self.target_count:,}")
        print(f"{'='*80}\n")
        
        for brand in self.brands:
            if len(self.data) >= self.target_count:
                break
                
            print(f"\n🔍 Scraping {brand.upper()} phones...")
            brand_url = f"{self.category_url}?q={brand}"
            self.scrape_category(brand_url, brand)
            
            if len(self.data) > 0:
                print(f"   ✅ Collected {len(self.data):,} total samples so far")
            
        print(f"\n✅ Scraped {len(self.data):,} mobile listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, brand):
        """Scrape a specific category/brand"""
        page = 1
        max_pages = 15
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{brand[:10]}", unit=" ads")
        
        consecutive_empty = 0
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(3, 6)
                
                # Wait for articles to load
                try:
                    articles = self.wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
                    )
                except TimeoutException:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                if not articles:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                consecutive_empty = 0
                found_on_page = 0
                
                for article in articles:
                    try:
                        ad_data = self.extract_listing_data(article, brand)
                        if ad_data and self.validate_data(ad_data):
                            self.data.append(ad_data)
                            found_on_page += 1
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except Exception as e:
                        continue
                
                if found_on_page == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 5:  # Increased from 3 to 5
                        break
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
        
        pbar.close()
    
    def extract_listing_data(self, article, brand):
        """Extract data from article element"""
        try:
            full_text = article.text
            
            # Extract title (first line usually)
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            if not lines:
                return None
            
            title = lines[0]
            
            # Extract price
            price = self.extract_price_from_text(full_text)
            if not price or price < 1000:
                return None
            
            # Extract URL
            try:
                link = article.find_element(By.TAG_NAME, "a")
                url = link.get_attribute('href')
            except:
                url = ""
            
            # Extract location (usually in the last few lines)
            location = lines[-1] if len(lines) > 1 else ""
            
            # Get description (join middle lines)
            description = " ".join(lines[1:-1]) if len(lines) > 2 else ""
            
            # NLP extraction
            nlp_features = NLPExtractor.extract_mobile_features(title, description)
            
            # Build data dictionary
            data = {
                'Title': title,
                'Price': price,
                'Brand': brand.title(),
                'Condition': nlp_features.get('condition', 'Used'),
                'Location': location,
                'Description': description,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat(),
                # NLP extracted features
                'RAM': nlp_features.get('ram'),
                'Storage': nlp_features.get('storage'),
                'Camera_MP': nlp_features.get('camera_mp'),
                'Battery_mAh': nlp_features.get('battery_mah'),
                'Screen_Size': nlp_features.get('screen_size'),
                'Is_5G': nlp_features.get('5g', 0),
                'PTA_Approved': nlp_features.get('pta_approved', 0),
                'Has_Warranty': nlp_features.get('warranty', 0),
                'Has_Box': nlp_features.get('box', 0)
            }
            
            return data
            
        except Exception as e:
            return None
    
    def validate_data(self, data):
        """Validate mobile listing"""
        # Must have valid price
        if not data['Price'] or data['Price'] < 1000 or data['Price'] > 1000000:
            return False
        
        # Must have at least one spec (RAM, Storage, or any number in title)
        title = data.get('Title', '').lower()
        has_spec = (
            data['RAM'] or 
            data['Storage'] or 
            bool(re.search(r'\d+gb|\d+/\d+', title))
        )
        
        return has_spec


class LaptopScraper(OLXScraper):
    """Scraper for laptops"""
    
    def __init__(self, target_count=5000, headless=False):
        super().__init__(headless)
        self.target_count = target_count
        self.category_url = f"{self.base_url}/computers-accessories/laptops_c1627"
        self.brands = ['dell', 'hp', 'lenovo', 'acer', 'asus', 'apple', 
                       'msi', 'microsoft', 'razer', 'alienware']
        
    def scrape(self):
        """Scrape laptop listings"""
        print(f"\n{'='*80}")
        print(f"💻 SCRAPING LAPTOPS - Target: {self.target_count:,}")
        print(f"{'='*80}\n")
        
        for brand in self.brands:
            if len(self.data) >= self.target_count:
                break
                
            print(f"\n🔍 Scraping {brand.upper()} laptops...")
            brand_url = f"{self.category_url}?q={brand}"
            self.scrape_category(brand_url, brand)
            
            if len(self.data) > 0:
                print(f"   ✅ Collected {len(self.data):,} total samples so far")
            
        print(f"\n✅ Scraped {len(self.data):,} laptop listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, brand):
        """Scrape a specific category/brand"""
        page = 1
        max_pages = 15
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{brand[:10]}", unit=" ads")
        
        consecutive_empty = 0
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(3, 6)
                
                try:
                    articles = self.wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
                    )
                except TimeoutException:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                if not articles:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                consecutive_empty = 0
                found_on_page = 0
                
                for article in articles:
                    try:
                        ad_data = self.extract_listing_data(article, brand)
                        if ad_data and self.validate_data(ad_data):
                            self.data.append(ad_data)
                            found_on_page += 1
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except:
                        continue
                
                if found_on_page == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
        
        pbar.close()
    
    def extract_listing_data(self, article, brand):
        """Extract data from article element"""
        try:
            full_text = article.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            if not lines:
                return None
            
            title = lines[0]
            
            # Extract price
            price = self.extract_price_from_text(full_text)
            if not price:
                return None
            
            # Fix thousand-prices
            if price < 1000:
                price = price * 1000
            
            # Extract URL
            try:
                link = article.find_element(By.TAG_NAME, "a")
                url = link.get_attribute('href')
            except:
                url = ""
            
            location = lines[-1] if len(lines) > 1 else ""
            description = " ".join(lines[1:-1]) if len(lines) > 2 else ""
            
            # NLP extraction
            nlp_features = NLPExtractor.extract_laptop_features(title, description)
            
            data = {
                'Title': title,
                'Price': price,
                'Brand': brand.title(),
                'Condition': nlp_features.get('condition', 'Used'),
                'Location': location,
                'Description': description,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat(),
                # NLP extracted features
                'Processor_Tier': nlp_features.get('processor_tier'),
                'Processor_Name': nlp_features.get('processor_name', ''),
                'Generation': nlp_features.get('generation'),
                'RAM': nlp_features.get('ram'),
                'Storage': nlp_features.get('storage'),
                'GPU_Tier': nlp_features.get('gpu_tier', 0),
                'GPU_Name': nlp_features.get('gpu_name', ''),
                'Screen_Size': nlp_features.get('screen_size'),
                'Is_Gaming': nlp_features.get('gaming', 0),
                'Is_Touchscreen': nlp_features.get('touchscreen', 0),
                'Has_SSD': nlp_features.get('ssd', 0)
            }
            
            return data
            
        except Exception as e:
            return None
    
    def validate_data(self, data):
        """Validate laptop listing"""
        if not data['Price'] or data['Price'] < 5000 or data['Price'] > 2000000:
            return False
        
        # Must have at least one spec indicator (processor, RAM, or typical laptop keywords)
        title = data.get('Title', '').lower()
        has_spec = (
            data['Processor_Tier'] or 
            data['RAM'] or 
            bool(re.search(r'i\d|ryzen|core|gb|generation|gen|\d{3,4}gb|laptop', title))
        )
        
        return has_spec


class FurnitureScraper(OLXScraper):
    """Scraper for furniture"""
    
    def __init__(self, target_count=5000, headless=False):
        super().__init__(headless)
        self.target_count = target_count
        self.category_url = f"{self.base_url}/furniture-home-decor_c4"
        self.categories = ['sofa', 'bed', 'table', 'chair', 'dining', 
                          'wardrobe', 'cabinet', 'desk', 'shelf', 'dresser']
        
    def scrape(self):
        """Scrape furniture listings"""
        print(f"\n{'='*80}")
        print(f"🪑 SCRAPING FURNITURE - Target: {self.target_count:,}")
        print(f"{'='*80}\n")
        
        for category in self.categories:
            if len(self.data) >= self.target_count:
                break
                
            print(f"\n🔍 Scraping {category.upper()}...")
            cat_url = f"{self.category_url}?q={category}"
            self.scrape_category(cat_url, category)
            
            if len(self.data) > 0:
                print(f"   ✅ Collected {len(self.data):,} total samples so far")
            
        print(f"\n✅ Scraped {len(self.data):,} furniture listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, category):
        """Scrape a specific category"""
        page = 1
        max_pages = 15
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{category[:10]}", unit=" ads")
        
        consecutive_empty = 0
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(3, 6)
                
                try:
                    articles = self.wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
                    )
                except TimeoutException:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                if not articles:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                consecutive_empty = 0
                found_on_page = 0
                
                for article in articles:
                    try:
                        ad_data = self.extract_listing_data(article, category)
                        if ad_data and self.validate_data(ad_data):
                            self.data.append(ad_data)
                            found_on_page += 1
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except:
                        continue
                
                if found_on_page == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
        
        pbar.close()
    
    def extract_listing_data(self, article, category):
        """Extract data from article element"""
        try:
            full_text = article.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            if not lines:
                return None
            
            title = lines[0]
            
            # Extract price
            price = self.extract_price_from_text(full_text)
            if not price:
                return None
            
            # Fix thousand-prices
            if price < 1000:
                price = price * 1000
            
            # Extract URL
            try:
                link = article.find_element(By.TAG_NAME, "a")
                url = link.get_attribute('href')
            except:
                url = ""
            
            location = lines[-1] if len(lines) > 1 else ""
            description = " ".join(lines[1:-1]) if len(lines) > 2 else ""
            
            # NLP extraction
            nlp_features = NLPExtractor.extract_furniture_features(title, description)
            
            data = {
                'Title': title,
                'Price': price,
                'Type': category.title(),
                'Condition': nlp_features.get('condition', 'Used'),
                'Location': location,
                'Description': description,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat(),
                # NLP extracted features
                'Material': nlp_features.get('material', 'Other'),
                'Material_Score': nlp_features.get('material_score', 5),
                'Seating_Capacity': nlp_features.get('seating_capacity'),
                'Length': nlp_features.get('length'),
                'Width': nlp_features.get('width'),
                'Height': nlp_features.get('height'),
                'Is_Imported': nlp_features.get('imported', 0),
                'Is_Handmade': nlp_features.get('handmade', 0),
                'Has_Storage': nlp_features.get('storage', 0),
                'Is_Modern': nlp_features.get('modern', 0),
                'Is_Antique': nlp_features.get('antique', 0)
            }
            
            return data
            
        except Exception as e:
            return None
    
    def validate_data(self, data):
        """Validate furniture listing"""
        if not data['Price'] or data['Price'] < 1000 or data['Price'] > 2000000:
            return False
        
        return True


def main():
    """Main scraping function"""
    print("\n" + "="*80)
    print("🚀 OLX PAKISTAN ROBUST SCRAPER WITH NLP EXTRACTION")
    print("   Target: 5000+ samples per category")
    print("="*80)
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    
    # Scrape Mobiles
    print("\n⏳ Starting Mobile scraping...")
    try:
        mobile_scraper = MobileScraper(target_count=5000, headless=False)
        mobile_df = mobile_scraper.scrape()
        mobile_scraper.close()
        
        if len(mobile_df) > 0:
            mobile_file = output_dir / f'mobile_scraped_{date_str}.csv'
            mobile_df.to_csv(mobile_file, index=False)
            results['mobile'] = len(mobile_df)
            print(f"\n✅ Saved {len(mobile_df):,} mobiles to: {mobile_file}")
        else:
            results['mobile'] = 0
            print(f"\n❌ No mobile data collected")
    except Exception as e:
        print(f"\n❌ Mobile scraping failed: {e}")
        results['mobile'] = 0
    
    # Scrape Laptops
    print("\n⏳ Starting Laptop scraping...")
    try:
        laptop_scraper = LaptopScraper(target_count=5000, headless=False)
        laptop_df = laptop_scraper.scrape()
        laptop_scraper.close()
        
        if len(laptop_df) > 0:
            laptop_file = output_dir / f'laptop_scraped_{date_str}.csv'
            laptop_df.to_csv(laptop_file, index=False)
            results['laptop'] = len(laptop_df)
            print(f"\n✅ Saved {len(laptop_df):,} laptops to: {laptop_file}")
        else:
            results['laptop'] = 0
            print(f"\n❌ No laptop data collected")
    except Exception as e:
        print(f"\n❌ Laptop scraping failed: {e}")
        results['laptop'] = 0
    
    # Scrape Furniture
    print("\n⏳ Starting Furniture scraping...")
    try:
        furniture_scraper = FurnitureScraper(target_count=5000, headless=False)
        furniture_df = furniture_scraper.scrape()
        furniture_scraper.close()
        
        if len(furniture_df) > 0:
            furniture_file = output_dir / f'furniture_scraped_{date_str}.csv'
            furniture_df.to_csv(furniture_file, index=False)
            results['furniture'] = len(furniture_df)
            print(f"\n✅ Saved {len(furniture_df):,} furniture to: {furniture_file}")
        else:
            results['furniture'] = 0
            print(f"\n❌ No furniture data collected")
    except Exception as e:
        print(f"\n❌ Furniture scraping failed: {e}")
        results['furniture'] = 0
    
    # Summary
    print("\n" + "="*80)
    print("🎉 SCRAPING COMPLETE")
    print("="*80)
    print(f"📱 Mobiles:   {results.get('mobile', 0):,} listings")
    print(f"💻 Laptops:   {results.get('laptop', 0):,} listings")
    print(f"🪑 Furniture: {results.get('furniture', 0):,} listings")
    print(f"📁 Saved to: {output_dir}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
