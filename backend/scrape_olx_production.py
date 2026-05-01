"""
Production-Ready OLX Pakistan Scraper
Scrapes 5000+ samples per category with robust error handling and NLP extraction
"""

import time
import re
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from datetime import datetime
from pathlib import Path
import json
from tqdm import tqdm
import random

class OLXScraper:
    """Base scraper for OLX Pakistan"""
    
    def __init__(self, headless=True):
        self.setup_driver(headless)
        self.base_url = "https://www.olx.com.pk"
        self.data = []
        
    def setup_driver(self, headless):
        """Setup undetected Chrome driver with stealth"""
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Use undetected chromedriver with auto version detection
        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.wait = WebDriverWait(self.driver, 15)
        
        # Execute stealth scripts
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        })
        
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Random delay to avoid detection"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def safe_get_text(self, element, selector, by=By.CSS_SELECTOR):
        """Safely extract text from element"""
        try:
            return element.find_element(by, selector).text.strip()
        except:
            return ""
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove Rs, commas, and extract number
        match = re.search(r'([\d,]+)', price_text.replace(',', ''))
        return int(match.group(1)) if match else None
    
    def close(self):
        """Close driver"""
        self.driver.quit()


class MobileScraper(OLXScraper):
    """Scraper for mobile phones"""
    
    def __init__(self, target_count=5000, headless=True):
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
            
        print(f"\n✅ Scraped {len(self.data):,} mobile listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, brand):
        """Scrape a specific category/brand"""
        page = 1
        max_pages = 20  # Limit per brand
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{brand[:10]}", unit=" ads")
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(2, 4)
                
                # Scroll to load dynamic content
                self.driver.execute_script("window.scrollTo(0, 1000)")
                self.random_delay(1, 2)
                
                # Wait for article listings to load
                try:
                    listings = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
                    )
                except TimeoutException:
                    break
                
                if not listings or len(listings) < 5:  # If too few, page may be empty
                    break
                
                # Extract data from each listing
                for listing in listings:
                    try:
                        ad_data = self.extract_listing_data(listing, brand)
                        if ad_data and self.validate_mobile_data(ad_data):
                            self.data.append(ad_data)
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        continue
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                break
        
        pbar.close()
    
    def extract_listing_data(self, listing, brand):
        """Extract data from a single listing"""
        try:
            # Get the link element first (this is the most reliable)
            try:
                link_elem = listing.find_element(By.CSS_SELECTOR, "a[href*='/item/']")
                url = link_elem.get_attribute('href')
                title = link_elem.get_attribute('title') or ""
            except:
                return None
            
            if not title:
                return None
            
            # Get all text from the listing
            all_text = listing.text
            if not all_text:
                return None
            
            # Extract price from text (format: Rs 70,999 or Rs 1.68 Lac)
            price = None
            price_match = re.search(r'Rs\s*([\\d,.]+(?:\s*Lac)?)', all_text)
            if price_match:
                price_str = price_match.group(1)
                # Handle "Lac" format
                if 'Lac' in price_str:
                    price_str = price_str.replace('Lac', '').strip()
                    price = float(price_str.replace(',', '')) * 100000
                else:
                    price = float(price_str.replace(',', ''))
            
            if not price or price < 1000 or price > 10000000:
                return None
            
            # Extract location (appears after title, before time)
            # Format: "Title\\nLocation•time ago"
            location = ""
            lines = all_text.split('\\n')
            for i, line in enumerate(lines):
                if '•' in line and 'ago' in line.lower():
                    # Location is on this line before the •
                    location = line.split('•')[0].strip()
                    break
            
            return {
                'Title': title,
                'Price': int(price),
                'Brand': brand.title(),
                'Condition': self.extract_condition(title + ' ' + all_text),
                'Location': location,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def extract_condition(self, text):
        """Extract condition from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['new', 'brand new', 'sealed', 'unused']):
            return 'New'
        elif any(word in text_lower for word in ['excellent', 'mint', '10/10']):
            return 'Excellent'
        elif any(word in text_lower for word in ['good', '9/10', '8/10']):
            return 'Good'
        else:
            return 'Used'
    
    def validate_mobile_data(self, data):
        """Validate mobile listing has essential info"""
        title = data['Title'].lower()
        
        # Must have brand in title
        if data['Brand'].lower() not in title:
            return False
        
        # Must have some specs (RAM, GB, or model number)
        has_specs = bool(re.search(r'\d+\s*gb|\d+/\d+|\d{2,}', title))
        
        return has_specs and 1000 <= data['Price'] <= 1000000


class LaptopScraper(OLXScraper):
    """Scraper for laptops"""
    
    def __init__(self, target_count=5000, headless=True):
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
            
        print(f"\n✅ Scraped {len(self.data):,} laptop listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, brand):
        """Scrape a specific category/brand"""
        page = 1
        max_pages = 25
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{brand[:10]}", unit=" ads")
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(2, 4)
                
                try:
                    listings = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-aut-id='itemBox']"))
                    )
                except TimeoutException:
                    break
                
                if not listings:
                    break
                
                for listing in listings:
                    try:
                        ad_data = self.extract_listing_data(listing, brand)
                        if ad_data and self.validate_laptop_data(ad_data):
                            self.data.append(ad_data)
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except:
                        continue
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                break
        
        pbar.close()
    
    def extract_listing_data(self, listing, brand):
        """Extract data from a single listing"""
        try:
            title = self.safe_get_text(listing, "span[data-aut-id='itemTitle']")
            if not title:
                return None
            
            price_text = self.safe_get_text(listing, "span[data-aut-id='itemPrice']")
            price = self.extract_price(price_text)
            if not price:
                return None
            
            # Fix thousand-prices
            if price < 1000:
                price = price * 1000
            
            try:
                url_elem = listing.find_element(By.CSS_SELECTOR, "a[data-aut-id='itemTitle']")
                url = url_elem.get_attribute('href')
            except:
                url = ""
            
            location = self.safe_get_text(listing, "span[data-aut-id='item-location']")
            desc = self.safe_get_text(listing, "div[data-aut-id='itemDescription']")
            
            # Extract model and type from title
            model = self.extract_model(title)
            laptop_type = self.extract_type(title + ' ' + desc)
            
            return {
                'Title': title,
                'Price': price,
                'Brand': brand.title(),
                'Model': model,
                'Condition': self.extract_condition(title + ' ' + desc),
                'Type': laptop_type,
                'Description': desc,
                'Location': location,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def extract_model(self, title):
        """Extract laptop model from title"""
        # Try to find model patterns
        patterns = [
            r'(inspiron|latitude|xps|pavilion|elitebook|thinkpad|ideapad|vivobook|tuf|rog)\s*[\w\d]+',
            r'(macbook|surface)\s*\w*',
            r'[A-Z]\d{3,4}[A-Z]*'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return 'Other'
    
    def extract_type(self, text):
        """Extract laptop type"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['gaming', 'rog', 'tuf', 'alienware', 'predator']):
            return 'Gaming'
        elif any(word in text_lower for word in ['business', 'elitebook', 'thinkpad', 'latitude']):
            return 'Business'
        elif any(word in text_lower for word in ['ultrabook', 'zenbook', 'swift']):
            return 'Ultrabook'
        else:
            return 'Standard'
    
    def extract_condition(self, text):
        """Extract condition from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['new', 'brand new', 'sealed', 'unused']):
            return 'New'
        elif any(word in text_lower for word in ['excellent', 'mint', '10/10']):
            return 'Excellent'
        elif any(word in text_lower for word in ['good', '9/10', '8/10']):
            return 'Good'
        else:
            return 'Used'
    
    def validate_laptop_data(self, data):
        """Validate laptop listing"""
        title = data['Title'].lower()
        
        # Must have brand
        if data['Brand'].lower() not in title:
            return False
        
        # Must have some specs
        has_specs = bool(re.search(r'i\d|ryzen|core|gb|generation|gen|\d{3,4}gb', title))
        
        return has_specs and 5000 <= data['Price'] <= 2000000


class FurnitureScraper(OLXScraper):
    """Scraper for furniture"""
    
    def __init__(self, target_count=5000, headless=True):
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
            
        print(f"\n✅ Scraped {len(self.data):,} furniture listings")
        return pd.DataFrame(self.data)
    
    def scrape_category(self, url, category):
        """Scrape a specific category"""
        page = 1
        max_pages = 25
        
        pbar = tqdm(total=min(500, self.target_count - len(self.data)), 
                   desc=f"{category[:10]}", unit=" ads")
        
        while page <= max_pages and len(self.data) < self.target_count:
            try:
                page_url = f"{url}&page={page}"
                self.driver.get(page_url)
                self.random_delay(2, 4)
                
                try:
                    listings = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-aut-id='itemBox']"))
                    )
                except TimeoutException:
                    break
                
                if not listings:
                    break
                
                for listing in listings:
                    try:
                        ad_data = self.extract_listing_data(listing, category)
                        if ad_data and self.validate_furniture_data(ad_data):
                            self.data.append(ad_data)
                            pbar.update(1)
                            
                            if len(self.data) >= self.target_count:
                                break
                    except:
                        continue
                
                page += 1
                
            except Exception as e:
                print(f"\n⚠️ Error on page {page}: {str(e)[:50]}")
                break
        
        pbar.close()
    
    def extract_listing_data(self, listing, category):
        """Extract data from a single listing"""
        try:
            title = self.safe_get_text(listing, "span[data-aut-id='itemTitle']")
            if not title:
                return None
            
            price_text = self.safe_get_text(listing, "span[data-aut-id='itemPrice']")
            price = self.extract_price(price_text)
            if not price:
                return None
            
            # Fix thousand-prices
            if price < 1000:
                price = price * 1000
            
            try:
                url_elem = listing.find_element(By.CSS_SELECTOR, "a[data-aut-id='itemTitle']")
                url = url_elem.get_attribute('href')
            except:
                url = ""
            
            location = self.safe_get_text(listing, "span[data-aut-id='item-location']")
            desc = self.safe_get_text(listing, "div[data-aut-id='itemDescription']")
            
            return {
                'Title': title,
                'Price': price,
                'Description': desc,
                'Condition': self.extract_condition(title + ' ' + desc),
                'Type': category.title(),
                'Material': self.extract_material(title + ' ' + desc),
                'Location': location,
                'URL': url,
                'Scraped_Date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def extract_material(self, text):
        """Extract material from text"""
        text_lower = text.lower()
        materials = {
            'wood': ['wood', 'wooden', 'sheesham', 'teak', 'oak', 'pine'],
            'metal': ['metal', 'steel', 'iron', 'aluminum'],
            'leather': ['leather', 'rexine'],
            'fabric': ['fabric', 'cloth', 'velvet'],
            'plastic': ['plastic'],
            'glass': ['glass'],
            'mdf': ['mdf', 'particle board']
        }
        
        for material, keywords in materials.items():
            if any(keyword in text_lower for keyword in keywords):
                return material.title()
        
        return 'Other'
    
    def extract_condition(self, text):
        """Extract condition from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['new', 'brand new', 'unused']):
            return 'New'
        elif any(word in text_lower for word in ['excellent', 'mint', '10/10']):
            return 'Excellent'
        elif any(word in text_lower for word in ['good', '9/10', '8/10']):
            return 'Good'
        else:
            return 'Used'
    
    def validate_furniture_data(self, data):
        """Validate furniture listing"""
        # Must have reasonable price
        return 1000 <= data['Price'] <= 2000000


def main():
    """Main scraping function"""
    print("\n" + "="*80)
    print("🚀 OLX PAKISTAN PRODUCTION SCRAPER")
    print("   Scraping 5000+ samples per category")
    print("="*80)
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    
    # Scrape Mobiles
    try:
        mobile_scraper = MobileScraper(target_count=5000, headless=False)
        mobile_df = mobile_scraper.scrape()
        mobile_scraper.close()
        
        mobile_file = output_dir / f'mobile_scraped_{date_str}.csv'
        mobile_df.to_csv(mobile_file, index=False)
        results['mobile'] = len(mobile_df)
        print(f"✅ Saved {len(mobile_df):,} mobiles to: {mobile_file}")
    except Exception as e:
        print(f"❌ Mobile scraping failed: {e}")
        results['mobile'] = 0
    
    # Scrape Laptops
    try:
        laptop_scraper = LaptopScraper(target_count=5000, headless=False)
        laptop_df = laptop_scraper.scrape()
        laptop_scraper.close()
        
        laptop_file = output_dir / f'laptop_scraped_{date_str}.csv'
        laptop_df.to_csv(laptop_file, index=False)
        results['laptop'] = len(laptop_df)
        print(f"✅ Saved {len(laptop_df):,} laptops to: {laptop_file}")
    except Exception as e:
        print(f"❌ Laptop scraping failed: {e}")
        results['laptop'] = 0
    
    # Scrape Furniture
    try:
        furniture_scraper = FurnitureScraper(target_count=5000, headless=False)
        furniture_df = furniture_scraper.scrape()
        furniture_scraper.close()
        
        furniture_file = output_dir / f'furniture_scraped_{date_str}.csv'
        furniture_df.to_csv(furniture_file, index=False)
        results['furniture'] = len(furniture_df)
        print(f"✅ Saved {len(furniture_df):,} furniture to: {furniture_file}")
    except Exception as e:
        print(f"❌ Furniture scraping failed: {e}")
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
