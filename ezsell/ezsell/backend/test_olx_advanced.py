"""
Advanced OLX Structure Test - Find correct selectors with stealth
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

def setup_stealth_driver():
    """Setup undetected Chrome with maximum stealth"""
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # Let undetected-chromedriver auto-detect the Chrome version
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    # Stealth scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    
    return driver

def test_selectors(driver, url):
    """Test various selector patterns"""
    print(f"\nLoading: {url}")
    driver.get(url)
    
    # Random human-like delay
    time.sleep(random.uniform(3, 5))
    
    # Scroll down slowly (human behavior)
    driver.execute_script("window.scrollTo(0, 500)")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 1000)")
    time.sleep(1)
    
    print("\n" + "="*80)
    print("PAGE ANALYSIS")
    print("="*80)
    
    # Check page title
    title = driver.title
    print(f"\n📄 Page Title: {title}")
    
    # Check if error page
    if "error" in title.lower() or "404" in title:
        print("⚠️  WARNING: Error page detected!")
        return False
    
    # Wait for page to load
    time.sleep(3)
    
    # Test multiple selector strategies
    selectors = {
        "Data attribute listing": "li[data-aut-id='itemBox']",
        "Generic list items": "li",
        "Article tags": "article",
        "Div with href": "div a[href*='/item/']",
        "Any link with item": "a[href*='/item/']",
        "Data-testid": "[data-testid*='listing']",
        "Class containing ad": "[class*='ad-']",
        "Class containing item": "[class*='item']",
        "Class containing listing": "[class*='listing']",
    }
    
    found_any = False
    for desc, selector in selectors.items():
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            count = len(elements)
            if count > 0:
                print(f"✅ {desc} ({selector}): Found {count} elements")
                found_any = True
                
                # Try to extract data from first element
                if count > 0:
                    try:
                        first = elements[0]
                        print(f"   Sample HTML: {first.get_attribute('outerHTML')[:200]}...")
                    except:
                        pass
            else:
                print(f"❌ {desc} ({selector}): Found 0 elements")
        except Exception as e:
            print(f"❌ {desc} ({selector}): Error - {str(e)[:50]}")
    
    if not found_any:
        print("\n⚠️  NO ELEMENTS FOUND WITH ANY SELECTOR!")
        print("\n📝 Saving page source for manual inspection...")
        with open('scraped_data/olx_page_stealth.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 Saved to: scraped_data/olx_page_stealth.html")
    
    return found_any

def main():
    print("="*80)
    print("🔍 ADVANCED OLX STRUCTURE TEST WITH STEALTH")
    print("="*80)
    
    driver = setup_stealth_driver()
    
    try:
        # Test mobile phones page
        url = "https://www.olx.com.pk/mobile-phones_c1453?q=samsung"
        success = test_selectors(driver, url)
        
        if success:
            print("\n✅ Successfully found listing elements!")
        else:
            print("\n❌ Failed to find listing elements - OLX may still be blocking")
        
        print("\n👀 Browser will stay open for 10 seconds for manual inspection...")
        time.sleep(10)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
