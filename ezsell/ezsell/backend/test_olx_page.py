"""Test OLX page accessibility"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

# Test URLs
urls = [
    "https://www.olx.com.pk/computers-accessories/laptops_c1627",
    "https://www.olx.com.pk/computers-accessories/laptops_c1627?q=dell",
    "https://www.olx.com.pk/mobile-phones_c1453"
]

print("\n🔍 Testing OLX Page Accessibility...\n")

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = uc.Chrome(options=options)

for url in urls:
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print('='*80)
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Check page title
        print(f"✅ Page title: {driver.title}")
        
        # Check if error page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "not found" in page_text or "404" in page_text or "error" in page_text:
            print(f"❌ ERROR DETECTED in page")
            print(f"   Page text preview: {page_text[:500]}")
        else:
            print(f"✅ Page loaded successfully")
        
        # Count articles
        articles = driver.find_elements(By.TAG_NAME, "article")
        print(f"✅ Found {len(articles)} article elements")
        
        # Count links with /item/
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")
        print(f"✅ Found {len(links)} item links")
        
        # Get first few listings
        if articles:
            print(f"\n📋 First listing preview:")
            print(articles[0].text[:200])
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

driver.quit()
print("\n✅ Test complete")
