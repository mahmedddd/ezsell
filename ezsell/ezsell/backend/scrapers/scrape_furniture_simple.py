"""
Simple OLX Furniture Scraper - Matches existing CSV format
VERY LENIENT - collects all furniture listings
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


class SimpleFurnitureScraper:
    """Simple furniture scraper matching existing CSV structure"""
    
    # Example columns: Title, Price, Category, Condition, Material, Description, URL
    # (If your furniture.csv has different columns, adjust below accordingly)
    
    CONDITIONS = {
        'new': ['new', 'brand new', 'fresh', 'sealed', 'unopened', 'unused'],
        'excellent': ['excellent', 'mint', 'like new', '10/10', '9.5/10', 'pristine'],
        'good': ['good', 'working', '8/10', '7/10', 'clean'],
        'fair': ['fair', '6/10', '5/10', 'used'],
        'used': ['used', 'old']
    }
    MATERIALS = ['wood', 'metal', 'steel', 'iron', 'plastic', 'glass', 'leather', 'fabric', 'marble', 'foam', 'wicker', 'rattan']
    CATEGORIES = ['sofa', 'bed', 'table', 'chair', 'dining', 'wardrobe', 'cabinet', 'desk', 'shelf', 'dresser']
    
    def __init__(self, target=3000):
        self.target = target
        self.data = []
        self.base_url = "https://www.olx.com.pk/items/q-furniture"
        self.categories = self.CATEGORIES
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
    
    def extract_price(self, text):
        match = re.search(r'Rs[\s]*([0-9,]+)', text)
        if match:
            price_str = match.group(1).replace(',', '')
            price = int(price_str)
            if price < 1000:
                price *= 1000
            return price
        return None
    
    def extract_condition(self, text):
        text_lower = text.lower()
        for condition, keywords in self.CONDITIONS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return condition.title()
        return 'Used'
    
    def extract_material(self, text):
        text_lower = text.lower()
        for material in self.MATERIALS:
            if material in text_lower:
                return material.title()
        return ''
    
    def extract_category(self, text):
        text_lower = text.lower()
        for cat in self.CATEGORIES:
            if cat in text_lower:
                return cat.title()
        return 'Furniture'
    
    def scrape_category(self, category):
        cat_data = []
        url = f"{self.base_url}?q={category}"
        max_pages = 15
        consecutive_empty = 0
        pbar = tqdm(desc=f"{category}", total=200, unit=" ads")
        for page in range(1, max_pages + 1):
            if len(self.data) >= self.target:
                break
            page_url = f"{url}&page={page}"
            try:
                self.driver.get(page_url)
                time.sleep(random.uniform(3, 6))
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
                        article_text = article.text
                        link = article.find_element(By.TAG_NAME, "a")
                        item_url = link.get_attribute('href')
                        lines = [l.strip() for l in article_text.split('\n') if l.strip()]
                        if len(lines) < 2:
                            continue
                        title = lines[0]
                        price_text = lines[1]
                        price = self.extract_price(price_text)
                        if not price or price < 1000 or price > 2000000:
                            continue
                        condition = self.extract_condition(title + " " + " ".join(lines))
                        material = self.extract_material(title + " " + " ".join(lines))
                        category_val = self.extract_category(title + " " + " ".join(lines))
                        description = " ".join(lines[2:]) if len(lines) > 2 else ""
                        data = {
                            'Title': title,
                            'Price': price,
                            'Category': category_val,
                            'Condition': condition,
                            'Material': material,
                            'Description': description,
                            'URL': item_url
                        }
                        self.data.append(data)
                        cat_data.append(data)
                        page_collected += 1
                        pbar.update(1)
                    except Exception as e:
                        continue
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"\n   ⚠️  Error on page {page}: {e}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
        pbar.close()
        print(f"   ✅ {category.upper()}: {len(cat_data)} items")
        return cat_data
    
    def scrape_all(self):
        print("\n" + "="*80)
        print("🚀 SIMPLE OLX FURNITURE SCRAPER")
        print("="*80)
        print(f"📊 Target: {self.target:,} furniture listings")
        print(f"🔍 Categories: {len(self.categories)}")
        print("="*80 + "\n")
        for category in self.categories:
            if len(self.data) >= self.target:
                break
            print(f"\n🔍 Scraping {category.upper()}...")
            self.scrape_category(category)
            print(f"   📊 Total collected: {len(self.data):,}")
        self.driver.quit()
        df = pd.DataFrame(self.data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data/furniture_scraped_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print("\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE!")
        print("="*80)
        print(f"📊 Total: {len(df):,} furniture listings")
        print(f"💰 Price range: Rs.{df['Price'].min():,.0f} - Rs.{df['Price'].max():,.0f}")
        print(f"📁 Saved to: {filename}")
        print("\n📊 Category Distribution:")
        for cat, count in df['Category'].value_counts().items():
            print(f"   {cat}: {count}")
        print("\n📊 Condition Distribution:")
        for cond, count in df['Condition'].value_counts().items():
            print(f"   {cond}: {count}")
        return df

def main():
    scraper = SimpleFurnitureScraper(target=3000)
    df = scraper.scrape_all()
    print(f"\n✅ Final dataset: {len(df):,} rows × {len(df.columns)} columns")

if __name__ == "__main__":
    main()
