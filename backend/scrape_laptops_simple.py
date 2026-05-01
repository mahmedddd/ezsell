"""
Simple OLX Laptop Scraper - Matches existing CSV format
VERY LENIENT - collects all laptop listings
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time
import random
from tqdm import tqdm
from datetime import datetime


class SimpleLaptopScraper:
    """Simple laptop scraper matching existing CSV structure"""
    
    # CSV columns: Title, Price, Brand, Model, Condition, Type, Description, URL
    
    CONDITIONS = {
        'new': ['new', 'brand new', 'fresh', 'sealed', 'unopened', 'unused'],
        'excellent': ['excellent', 'mint', 'like new', '10/10', '9.5/10', 'pristine'],
        'good': ['good', 'working', '8/10', '7/10', 'clean'],
        'fair': ['fair', '6/10', '5/10', 'used'],
        'used': ['used', 'old']
    }
    
    def __init__(self, target=5000):
        self.target = target
        self.data = []
        self.base_url = "https://www.olx.com.pk/items/q-laptop"
        
        # 12 brands to scrape
        self.brands = ['dell', 'hp', 'lenovo', 'acer', 'asus', 'apple', 
                       'msi', 'microsoft', 'razer', 'alienware', 'lg', 'toshiba']
        
        # Setup undetected chrome
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
    
    def extract_price(self, text):
        """Extract price from text"""
        match = re.search(r'Rs[\s]*([0-9,]+)', text)
        if match:
            price_str = match.group(1).replace(',', '')
            price = int(price_str)
            # Auto-multiply if looks like thousands
            if price < 1000:
                price *= 1000
            return price
        return None
    
    def extract_condition(self, text):
        """Extract condition from text"""
        text_lower = text.lower()
        for condition, keywords in self.CONDITIONS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return condition.title()
        return 'Used'
    
    def extract_model(self, text):
        """Extract model from title"""
        text_lower = text.lower()
        
        # Look for processor models
        processors = {
            'i9': 'Core i9', 'i7': 'Core i7', 'i5': 'Core i5', 'i3': 'Core i3',
            'ryzen 9': 'Ryzen 9', 'ryzen 7': 'Ryzen 7', 'ryzen 5': 'Ryzen 5',
            'm3': 'M3', 'm2': 'M2', 'm1': 'M1'
        }
        
        for key, name in processors.items():
            if key in text_lower:
                # Try to extract generation
                gen_match = re.search(rf'{key}[- ]?(\d{{1,2}})', text_lower)
                if gen_match:
                    return f"{name} {gen_match.group(1)}th Gen"
                return name
        
        return ""
    
    def extract_type(self, text):
        """Determine laptop type"""
        text_lower = text.lower()
        if 'gaming' in text_lower:
            return 'Gaming'
        elif 'business' in text_lower or 'workstation' in text_lower:
            return 'Business'
        elif 'ultrabook' in text_lower or 'macbook' in text_lower:
            return 'Ultrabook'
        return 'Laptop'
    
    def scrape_brand(self, brand):
        """Scrape laptops for a specific brand"""
        brand_data = []
        url = f"{self.base_url}?q={brand}"
        
        max_pages = 20
        consecutive_empty = 0
        
        pbar = tqdm(desc=f"{brand}", total=500, unit=" ads")
        
        for page in range(1, max_pages + 1):
            if len(self.data) >= self.target:
                break
            
            page_url = f"{url}&page={page}"
            
            try:
                self.driver.get(page_url)
                time.sleep(random.uniform(3, 6))
                
                # Wait for articles
                articles = self.wait.until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
                )
                
                if not articles:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    continue
                
                consecutive_empty = 0
                page_collected = 0
                
                for article in articles:
                    if len(self.data) >= self.target:
                        break
                    
                    try:
                        # Extract text from article
                        article_text = article.text
                        
                        # Get URL
                        link = article.find_element(By.TAG_NAME, "a")
                        item_url = link.get_attribute('href')
                        
                        # Parse text
                        lines = [l.strip() for l in article_text.split('\n') if l.strip()]
                        
                        if len(lines) < 2:
                            continue
                        
                        title = lines[0]
                        price_text = lines[1]
                        
                        # Extract price
                        price = self.extract_price(price_text)
                        
                        # VERY LENIENT VALIDATION - just check price exists
                        if not price or price < 1000 or price > 5000000:
                            continue
                        
                        # Extract other fields
                        condition = self.extract_condition(title + " " + " ".join(lines))
                        model = self.extract_model(title)
                        laptop_type = self.extract_type(title)
                        description = " ".join(lines[2:]) if len(lines) > 2 else ""
                        
                        # Create data record - MATCH EXISTING CSV
                        data = {
                            'Title': title,
                            'Price': price,
                            'Brand': brand.title(),
                            'Model': model,
                            'Condition': condition,
                            'Type': laptop_type,
                            'Description': description,
                            'URL': item_url
                        }
                        
                        self.data.append(data)
                        brand_data.append(data)
                        page_collected += 1
                        pbar.update(1)
                        
                    except Exception as e:
                        continue
                
                # Small delay between pages
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"\n   ⚠️  Error on page {page}: {e}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
        
        pbar.close()
        print(f"   ✅ {brand.upper()}: {len(brand_data)} laptops")
        return brand_data
    
    def scrape_all(self):
        """Scrape all brands"""
        print("\n" + "="*80)
        print("🚀 SIMPLE OLX LAPTOP SCRAPER")
        print("="*80)
        print(f"📊 Target: {self.target:,} laptop listings")
        print(f"🔍 Brands: {len(self.brands)}")
        print("="*80 + "\n")
        
        for brand in self.brands:
            if len(self.data) >= self.target:
                break
            
            print(f"\n🔍 Scraping {brand.upper()} laptops...")
            self.scrape_brand(brand)
            print(f"   📊 Total collected: {len(self.data):,}")
        
        self.driver.quit()
        
        # Create dataframe
        df = pd.DataFrame(self.data)
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data/laptop_scraped_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE!")
        print("="*80)
        print(f"📊 Total: {len(df):,} laptop listings")
        print(f"💰 Price range: Rs.{df['Price'].min():,.0f} - Rs.{df['Price'].max():,.0f}")
        print(f"📁 Saved to: {filename}")
        
        # Brand distribution
        print("\n📊 Brand Distribution:")
        for brand, count in df['Brand'].value_counts().items():
            print(f"   {brand}: {count}")
        
        # Condition distribution
        print("\n📊 Condition Distribution:")
        for cond, count in df['Condition'].value_counts().items():
            print(f"   {cond}: {count}")
        
        return df


def main():
    scraper = SimpleLaptopScraper(target=5000)
    df = scraper.scrape_all()
    print(f"\n✅ Final dataset: {len(df):,} rows × {len(df.columns)} columns")


if __name__ == "__main__":
    main()
