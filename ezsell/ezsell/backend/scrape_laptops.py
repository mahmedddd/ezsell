"""
Laptop-only scraper with robust NLP extraction
"""
import time
import re
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import random
import undetected_chromedriver as uc

class NLPExtractor:
    """NLP-based feature extraction for laptops"""
    
    PROCESSOR_PATTERNS = {
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
        'pentium': (r'\bpentium\b', 2),
        'core': (r'\bcore\b', 5)
    }
    
    GPU_PATTERNS = {
        'rtx 4090': (r'\brtx\s*4090\b', 10),
        'rtx 4080': (r'\brtx\s*4080\b', 9),
        'rtx 4070': (r'\brtx\s*4070\b', 9),
        'rtx 4060': (r'\brtx\s*4060\b', 8),
        'rtx 3080': (r'\brtx\s*3080\b', 8),
        'rtx 3070': (r'\brtx\s*3070\b', 8),
        'rtx 3060': (r'\brtx\s*3060\b', 7),
        'rtx 3050': (r'\brtx\s*3050\b', 6),
        'gtx 1660': (r'\bgtx\s*1660\b', 6),
        'gtx 1650': (r'\bgtx\s*1650\b', 5),
        'gtx 1050': (r'\bgtx\s*1050\b', 4),
        'mx550': (r'\bmx\s*550\b', 3),
        'mx450': (r'\bmx\s*450\b', 3),
        'mx350': (r'\bmx\s*350\b', 2),
        'integrated': (r'\bintegrated\b|\buhd\b|\biris\b', 1)
    }
    
    CONDITIONS = {
        'new': ['new', 'brand new', 'sealed', 'unused', '10/10', 'mint condition'],
        'excellent': ['excellent', '9.5/10', '9/10', 'like new', 'barely used', 'mint'],
        'good': ['good', '8/10', '8.5/10', 'working perfectly', 'good condition'],
        'fair': ['fair', '7/10', '6/10', 'minor issues', 'some wear'],
        'used': ['used', 'working', 'average']
    }
    
    @staticmethod
    def extract_laptop_features(title, description):
        """Extract comprehensive laptop features"""
        text = f"{title} {description}".lower()
        features = {}
        
        # Processor
        features['processor_tier'] = 5
        features['processor_name'] = ''
        for name, (pattern, tier) in NLPExtractor.PROCESSOR_PATTERNS.items():
            if re.search(pattern, text):
                features['processor_tier'] = tier
                features['processor_name'] = name
                break
        
        # Generation
        gen_match = re.search(r'(\d+)(?:th|nd|rd|st)?\s*gen(?:eration)?', text)
        if gen_match:
            features['generation'] = int(gen_match.group(1))
        else:
            features['generation'] = None
        
        # RAM - multiple patterns
        ram_patterns = [
            r'(\d+)\s*gb\s*ram',
            r'ram\s*(\d+)\s*gb',
            r'(\d+)\s*gb\s*ddr',
            r'ddr\d+\s*(\d+)\s*gb'
        ]
        features['ram'] = None
        for pattern in ram_patterns:
            ram_match = re.search(pattern, text)
            if ram_match:
                features['ram'] = int(ram_match.group(1))
                break
        
        # Storage - look for SSD/HDD
        storage_patterns = [
            r'(\d{3,4})\s*gb\s*ssd',
            r'ssd\s*(\d{3,4})\s*gb',
            r'(\d{3,4})\s*gb\s*hdd',
            r'(\d{1,2})\s*tb\s*(?:ssd|hdd)',
            r'(\d{3,4})\s*gb\s*(?:storage|nvme|m\.?2)',
            r'(\d{3,4})gb'  # Fallback
        ]
        features['storage'] = None
        for pattern in storage_patterns:
            storage_match = re.search(pattern, text)
            if storage_match:
                val = int(storage_match.group(1))
                # Convert TB to GB
                if 'tb' in text[max(0, storage_match.start()-5):storage_match.end()+5].lower():
                    val = val * 1000
                features['storage'] = val
                break
        
        # GPU
        features['gpu_tier'] = 0
        features['gpu_name'] = ''
        for name, (pattern, tier) in NLPExtractor.GPU_PATTERNS.items():
            if re.search(pattern, text):
                features['gpu_tier'] = tier
                features['gpu_name'] = name
                break
        
        # Screen size
        screen_patterns = [
            r'(\d+\.?\d*)\s*(?:inch|")',
            r'(\d+)"',
            r'(\d{2})\s*inch'
        ]
        features['screen_size'] = None
        for pattern in screen_patterns:
            screen_match = re.search(pattern, text)
            if screen_match:
                features['screen_size'] = float(screen_match.group(1))
                break
        
        # Boolean features
        features['is_gaming'] = 1 if re.search(r'\bgaming\b|\brog\b|\btuf\b|\balienware\b|\bpredator\b', text) else 0
        features['is_touchscreen'] = 1 if re.search(r'\btouch\s*screen\b|\btouch\b', text) else 0
        features['has_ssd'] = 1 if re.search(r'\bssd\b', text) else 0
        features['has_backlit'] = 1 if re.search(r'\bbacklit\b|\brgb\b', text) else 0
        features['has_webcam'] = 1 if re.search(r'\bwebcam\b', text) else 0
        features['has_fingerprint'] = 1 if re.search(r'\bfingerprint\b', text) else 0
        features['is_convertible'] = 1 if re.search(r'\bconvertible\b|\b2\s*in\s*1\b', text) else 0
        
        # Condition
        features['condition'] = NLPExtractor.extract_condition(text)
        
        return features
    
    @staticmethod
    def extract_condition(text):
        """Extract condition from text"""
        for condition, keywords in NLPExtractor.CONDITIONS.items():
            if any(keyword in text for keyword in keywords):
                return condition.title()
        return 'Used'


class LaptopScraper:
    """Robust laptop scraper"""
    
    def __init__(self, target_count=5000, headless=False):
        self.target_count = target_count
        self.data = []
        self.base_url = "https://www.olx.com.pk"
        self.category_url = f"{self.base_url}/computers-accessories/laptops_c1627"
        self.brands = ['dell', 'hp', 'lenovo', 'acer', 'asus', 'apple', 
                       'msi', 'microsoft', 'razer', 'alienware', 'lg', 'toshiba']
        
        # Setup driver
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
    
    def random_delay(self, min_sec=2, max_sec=5):
        """Random delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def extract_price_from_text(self, text):
        """Extract price"""
        match = re.search(r'Rs[\s]*([0-9,]+)', text)
        if match:
            price_str = match.group(1).replace(',', '')
            return int(price_str)
        return None
    
    def scrape(self):
        """Scrape all brands"""
        print(f"\n{'='*80}")
        print(f"💻 SCRAPING LAPTOPS - Target: {self.target_count:,}")
        print(f"{'='*80}\n")
        
        for brand in self.brands:
            if len(self.data) >= self.target_count:
                break
            
            print(f"\n🔍 Scraping {brand.upper()} laptops...")
            brand_url = f"{self.category_url}?q={brand}"
            self.scrape_brand(brand_url, brand)
            
            if len(self.data) > 0:
                print(f"   ✅ Collected {len(self.data):,} total samples so far")
        
        print(f"\n✅ Scraped {len(self.data):,} laptop listings")
        return pd.DataFrame(self.data)
    
    def scrape_brand(self, url, brand):
        """Scrape specific brand"""
        page = 1
        max_pages = 20
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)),
                   desc=f"{brand[:10]}", unit=" ads")
        
        consecutive_empty = 0
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(3, 6)
                
                # Wait for articles
                try:
                    articles = self.wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
                    )
                except TimeoutException:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    page += 1
                    continue
                
                if not articles:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    page += 1
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
        """Extract data from article"""
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
                # NLP features
                'Processor_Tier': nlp_features.get('processor_tier'),
                'Processor_Name': nlp_features.get('processor_name', ''),
                'Generation': nlp_features.get('generation'),
                'RAM': nlp_features.get('ram'),
                'Storage': nlp_features.get('storage'),
                'GPU_Tier': nlp_features.get('gpu_tier', 0),
                'GPU_Name': nlp_features.get('gpu_name', ''),
                'Screen_Size': nlp_features.get('screen_size'),
                'Is_Gaming': nlp_features.get('is_gaming', 0),
                'Is_Touchscreen': nlp_features.get('is_touchscreen', 0),
                'Has_SSD': nlp_features.get('has_ssd', 0),
                'Has_Backlit': nlp_features.get('has_backlit', 0),
                'Has_Webcam': nlp_features.get('has_webcam', 0),
                'Has_Fingerprint': nlp_features.get('has_fingerprint', 0),
                'Is_Convertible': nlp_features.get('is_convertible', 0)
            }
            
            return data
            
        except Exception as e:
            return None
    
    def validate_data(self, data):
        """Validate laptop data - VERY LENIENT"""
        # Valid price range (very wide)
        if not data['Price'] or data['Price'] < 1000 or data['Price'] > 5000000:
            return False
        
        # Accept if has title longer than 5 characters
        return len(data['Title']) > 5
    
    def close(self):
        """Close driver"""
        self.driver.quit()


def main():
    """Main function"""
    print("\n" + "="*80)
    print("🚀 OLX LAPTOP SCRAPER - ROBUST NLP EXTRACTION")
    print("="*80)
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        scraper = LaptopScraper(target_count=5000, headless=False)
        df = scraper.scrape()
        scraper.close()
        
        if len(df) > 0:
            output_file = output_dir / f'laptop_scraped_{date_str}.csv'
            df.to_csv(output_file, index=False)
            
            print(f"\n{'='*80}")
            print(f"✅ SUCCESS - Saved {len(df):,} laptops")
            print(f"📁 File: {output_file}")
            print(f"{'='*80}\n")
            
            # Show sample stats
            print("📊 DATA SUMMARY:")
            print(f"   Price range: Rs.{df['Price'].min():,.0f} - Rs.{df['Price'].max():,.0f}")
            print(f"   Brands: {df['Brand'].nunique()} unique")
            print(f"   Conditions: {df['Condition'].value_counts().to_dict()}")
            print(f"   With RAM: {df['RAM'].notna().sum()} ({df['RAM'].notna().sum()/len(df)*100:.1f}%)")
            print(f"   With Storage: {df['Storage'].notna().sum()} ({df['Storage'].notna().sum()/len(df)*100:.1f}%)")
            print(f"   With GPU: {(df['GPU_Tier'] > 0).sum()} ({(df['GPU_Tier'] > 0).sum()/len(df)*100:.1f}%)")
            print(f"   Gaming: {df['Is_Gaming'].sum()} laptops")
            
        else:
            print("\n❌ No data collected")
            
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
