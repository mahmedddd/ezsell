"""
Production-Ready OLX Scraper with Selenium for Dynamic Content
Scrapes real listings from OLX Pakistan for all categories
"""

import time
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumOLXScraper:
    """Scraper using Selenium for JavaScript-rendered content"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Selenium WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            logger.info("Setting up Chrome WebDriver...")
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver setup complete")
            return True
            
        except ImportError:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def scrape_category(self, category: str, max_pages: int = 50) -> List[Dict]:
        """Scrape listings from OLX Pakistan"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Category URLs
        urls = {
            'mobile': 'https://www.olx.com.pk/mobile-phones/',
            'laptop': 'https://www.olx.com.pk/computers-accessories/laptops/',
            'furniture': 'https://www.olx.com.pk/furniture-home-decor/'
        }
        
        if category not in urls:
            logger.error(f"Invalid category: {category}")
            return []
        
        base_url = urls[category]
        all_listings = []
        
        logger.info(f"Starting {category} scraping from OLX Pakistan...")
        logger.info(f"Target: {max_pages} pages")
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{base_url}?page={page}"
                logger.info(f"Scraping page {page}: {url}")
                
                self.driver.get(url)
                time.sleep(3)  # Wait for page load
                
                # Wait for listings to appear
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-aut-id='itemBox']"))
                )
                
                # Get all listing cards
                listing_cards = self.driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
                logger.info(f"Found {len(listing_cards)} listings on page {page}")
                
                page_listings = []
                
                for idx, card in enumerate(listing_cards, 1):
                    try:
                        listing = self._extract_listing_data(card, category)
                        if listing and listing.get('price'):
                            page_listings.append(listing)
                            
                            if len(page_listings) % 10 == 0:
                                logger.info(f"  Extracted {len(page_listings)} listings so far...")
                                
                    except Exception as e:
                        logger.warning(f"Error extracting listing {idx}: {e}")
                        continue
                
                all_listings.extend(page_listings)
                logger.info(f"Page {page} complete: {len(page_listings)} listings extracted")
                logger.info(f"Total so far: {len(all_listings)} listings")
                
                # Stop if no listings found (end of pages)
                if len(page_listings) == 0:
                    logger.info(f"No listings found on page {page}. Stopping.")
                    break
                
                # Polite delay between pages
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                continue
        
        logger.info(f"Scraping complete: {len(all_listings)} total listings")
        return all_listings
    
    def _extract_listing_data(self, card, category: str) -> Optional[Dict]:
        """Extract data from a single listing card"""
        from selenium.webdriver.common.by import By
        
        try:
            # Title
            title_elem = card.find_element(By.CSS_SELECTOR, "[data-aut-id='itemTitle']")
            title = title_elem.text.strip() if title_elem else ""
            
            # Price
            price_elem = card.find_element(By.CSS_SELECTOR, "[data-aut-id='itemPrice']")
            price_text = price_elem.text.strip() if price_elem else ""
            price = self._parse_price(price_text)
            
            # Location
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, "[data-aut-id='item-location']")
                location = location_elem.text.strip()
            except:
                location = "Pakistan"
            
            # URL
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a[href]")
                url = link_elem.get_attribute('href')
            except:
                url = ""
            
            # Description (if available)
            try:
                desc_elem = card.find_element(By.CSS_SELECTOR, "[data-aut-id='itemDescription']")
                description = desc_elem.text.strip()
            except:
                description = title  # Fallback to title
            
            if not title or not price:
                return None
            
            listing = {
                'title': title,
                'price': price,
                'location': location,
                'description': description,
                'url': url,
                'scraped_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            return listing
            
        except Exception as e:
            logger.debug(f"Error extracting listing: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        import re
        
        if not price_text:
            return None
        
        # Remove "Rs" and commas
        price_text = price_text.replace('Rs', '').replace(',', '').strip()
        
        # Extract number
        match = re.search(r'(\d+\.?\d*)', price_text)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        
        return None
    
    def save_to_csv(self, listings: List[Dict], category: str, output_dir: str = 'scraped_data'):
        """Save scraped listings to CSV"""
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/{category}_scraped_{timestamp}.csv"
        
        df = pd.DataFrame(listings)
        df.to_csv(filename, index=False)
        
        logger.info(f"Saved {len(listings)} listings to {filename}")
        return filename
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")


def scrape_all_categories(max_pages_per_category: int = 50):
    """Scrape all categories"""
    
    logger.info("="*80)
    logger.info("STARTING FULL OLX SCRAPING")
    logger.info("="*80)
    
    scraper = SeleniumOLXScraper(headless=True)
    
    if not scraper.setup_driver():
        logger.error("Failed to setup driver. Aborting.")
        return
    
    categories = ['mobile', 'laptop', 'furniture']
    results = {}
    
    try:
        for category in categories:
            logger.info(f"\n{'='*80}")
            logger.info(f"SCRAPING {category.upper()}")
            logger.info(f"{'='*80}\n")
            
            listings = scraper.scrape_category(category, max_pages=max_pages_per_category)
            
            if listings:
                filename = scraper.save_to_csv(listings, category)
                results[category] = {
                    'count': len(listings),
                    'file': filename
                }
            else:
                logger.warning(f"No listings scraped for {category}")
                results[category] = {
                    'count': 0,
                    'file': None
                }
            
            # Delay between categories
            time.sleep(5)
    
    finally:
        scraper.close()
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SCRAPING SUMMARY")
    logger.info(f"{'='*80}")
    
    total = 0
    for category, result in results.items():
        count = result['count']
        total += count
        status = "✅" if count > 0 else "❌"
        logger.info(f"{status} {category.capitalize()}: {count:,} listings")
        if result['file']:
            logger.info(f"   File: {result['file']}")
    
    logger.info(f"\nTotal listings scraped: {total:,}")
    logger.info(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape OLX Pakistan listings')
    parser.add_argument('--category', type=str, choices=['mobile', 'laptop', 'furniture', 'all'],
                       default='all', help='Category to scrape')
    parser.add_argument('--pages', type=int, default=50,
                       help='Maximum pages to scrape per category')
    
    args = parser.parse_args()
    
    if args.category == 'all':
        scrape_all_categories(max_pages_per_category=args.pages)
    else:
        scraper = SeleniumOLXScraper(headless=True)
        if scraper.setup_driver():
            listings = scraper.scrape_category(args.category, max_pages=args.pages)
            if listings:
                scraper.save_to_csv(listings, args.category)
            scraper.close()
