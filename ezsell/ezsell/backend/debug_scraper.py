"""
Debug scraper to see what's being extracted
"""
import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

def setup_driver():
    """Setup undetected Chrome"""
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver

print("="*80)
print("🔍 DEBUG SCRAPER - See what's being extracted")
print("="*80)

driver = setup_driver()

try:
    url = "https://www.olx.com.pk/mobile-phones_c1453?q=samsung"
    print(f"\nLoading: {url}")
    driver.get(url)
    
    # Wait and scroll
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 1000)")
    time.sleep(2)
    
    # Find articles
    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    print(f"\n✅ Found {len(articles)} article elements")
    
    if articles:
        print("\n" + "="*80)
        print("FIRST 3 LISTINGS:")
        print("="*80)
        
        for i, article in enumerate(articles[:3]):
            print(f"\n--- Listing {i+1} ---")
            
            # Try to get link
            try:
                link = article.find_element(By.CSS_SELECTOR, "a[href*='/item/']")
                url = link.get_attribute('href')
                title = link.get_attribute('title')
                print(f"Title: {title}")
                print(f"URL: {url}")
            except Exception as e:
                print(f"❌ Link error: {e}")
            
            # Try to get price
            try:
                price_elem = article.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemPrice']")
                price_text = price_elem.text
                print(f"Price (data-aut-id): {price_text}")
            except:
                # Fallback: search all text
                all_text = article.text
                price_match = re.search(r'Rs[\\s,]?([\\d,]+)', all_text)
                if price_match:
                    print(f"Price (from text): Rs {price_match.group(1)}")
                else:
                    print("❌ No price found")
            
            # Try to get location
            try:
                loc_elem = article.find_element(By.CSS_SELECTOR, "span[data-aut-id='item-location']")
                location = loc_elem.text
                print(f"Location: {location}")
            except:
                print("❌ No location found")
            
            # Show all text
            print(f"All text: {article.text[:200]}...")
    
    print("\n" + "="*80)
    print("✅ Debug complete - browser will close in 5 seconds")
    time.sleep(5)
    
finally:
    driver.quit()
