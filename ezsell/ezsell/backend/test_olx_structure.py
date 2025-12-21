"""
Quick test to inspect OLX page structure
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup
chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

try:
    # Test mobile phones page
    url = "https://www.olx.com.pk/mobile-phones_c1453?q=samsung"
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("\n" + "="*80)
    print("PAGE STRUCTURE ANALYSIS")
    print("="*80)
    
    # Try to find listings with different selectors
    selectors_to_try = [
        ("li[data-aut-id='itemBox']", "Listing items"),
        ("li.EIR5N", "Listing items (class)"),
        ("div._95728", "Ad container"),
        ("div[data-aut-id]", "Any data-aut-id div"),
        ("a[data-aut-id='itemTitle']", "Title links"),
        ("span[data-aut-id='itemTitle']", "Title spans"),
        ("div._2tW1I", "Ad wrapper")
    ]
    
    for selector, desc in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"\n✅ {desc}: Found {len(elements)} elements")
            if elements and len(elements) > 0:
                print(f"   Sample HTML: {elements[0].get_attribute('outerHTML')[:200]}...")
        except Exception as e:
            print(f"\n❌ {desc}: {str(e)[:100]}")
    
    # Get page source sample
    print("\n" + "="*80)
    print("PAGE SOURCE SAMPLE (first 2000 chars)")
    print("="*80)
    print(driver.page_source[:2000])
    
    # Save full HTML for inspection
    with open('scraped_data/olx_page_sample.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("\n💾 Full page saved to: scraped_data/olx_page_sample.html")
    
    input("\nPress Enter to close browser...")
    
finally:
    driver.quit()
