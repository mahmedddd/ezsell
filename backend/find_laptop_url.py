"""Find correct OLX laptop category URL"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

print("\n🔍 Searching for correct laptop category URL...\n")

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = uc.Chrome(options=options)

# Try different URLs
test_urls = [
    "https://www.olx.com.pk/computers-laptops_c1658",  # Alternative
    "https://www.olx.com.pk/laptops_c1658",  # Short form
    "https://www.olx.com.pk/items/q-laptop",  # Search query
    "https://www.olx.com.pk/computers-accessories_c1497",  # Parent category
]

for url in test_urls:
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    
    try:
        driver.get(url)
        time.sleep(4)
        
        title = driver.title
        print(f"Title: {title}")
        
        if "not found" in title.lower() or "404" in title.lower():
            print("❌ NOT FOUND")
        else:
            articles = driver.find_elements(By.TAG_NAME, "article")
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")
            print(f"✅ WORKING! Found {len(articles)} articles, {len(links)} item links")
            
            if articles:
                print(f"\nFirst listing: {articles[0].text[:150]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

driver.quit()
print("\n✅ Search complete")
