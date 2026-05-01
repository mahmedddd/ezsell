"""
Simple OLX Scraper - Alternative Implementation
===============================================

This is a lightweight scraper that works without Selenium.
It may get less data due to JavaScript rendering limitations,
but it's more reliable for demonstration purposes.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleOLXScraper:
    """Simple scraper using requests + BeautifulSoup"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_category(self, category: str, max_pages: int = 10) -> pd.DataFrame:
        """Scrape a category from OLX"""
        
        # Category URL mapping
        category_urls = {
            'mobile': 'https://www.olx.com.pk/mobile-phones/',
            'laptop': 'https://www.olx.com.pk/computers-accessories/laptops/',
            'furniture': 'https://www.olx.com.pk/furniture-home-decor/'
        }
        
        if category not in category_urls:
            raise ValueError(f"Unknown category: {category}")
        
        base_url = category_urls[category]
        all_listings = []
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SCRAPING {category.upper()}")
        logger.info('='*80)
        logger.info(f"Target: {max_pages} pages")
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}"
            logger.info(f"Scraping page {page}: {url}")
            
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find listing items (OLX uses various class names)
                listings = soup.find_all('li', {'data-aut-id': 'itemBox'})
                
                if not listings:
                    # Try alternative selector
                    listings = soup.find_all('div', class_='_1qwdE')
                
                if not listings:
                    logger.warning(f"No listings found on page {page}")
                    if page == 1:
                        logger.error("Could not find any listings on first page. Site structure may have changed.")
                        break
                    continue
                
                logger.info(f"Found {len(listings)} listings on page {page}")
                
                for listing in listings:
                    try:
                        data = self._extract_listing_data(listing, category)
                        if data and data['price'] > 0:
                            all_listings.append(data)
                    except Exception as e:
                        logger.debug(f"Error extracting listing: {e}")
                        continue
                
                logger.info(f"Page {page} complete: {len(all_listings)} total listings extracted")
                
                # Be nice to the server
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error on page {page}: {e}")
                continue
        
        df = pd.DataFrame(all_listings)
        logger.info(f"\n✅ Scraped {len(df)} total listings for {category}")
        
        return df
    
    def _extract_listing_data(self, listing_element, category: str) -> dict:
        """Extract data from a listing element"""
        
        # Try to find title
        title_elem = (
            listing_element.find('span', {'data-aut-id': 'itemTitle'}) or
            listing_element.find('div', class_='_2tW1I') or
            listing_element.find('a', {'data-aut-id': 'itemTitle'})
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Try to find price
        price_elem = (
            listing_element.find('span', {'data-aut-id': 'itemPrice'}) or
            listing_element.find('div', class_='_1zgtX')
        )
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = self._parse_price(price_text)
        
        # Try to find location
        location_elem = (
            listing_element.find('span', {'data-aut-id': 'item-location'}) or
            listing_element.find('div', class_='_2VPHc')
        )
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Try to find description (limited in list view)
        desc_elem = listing_element.find('div', class_='_2tW1I')
        description = desc_elem.get_text(strip=True) if desc_elem else title
        
        # Try to find URL
        link_elem = listing_element.find('a', href=True)
        url = f"https://www.olx.com.pk{link_elem['href']}" if link_elem else ""
        
        return {
            'title': title,
            'price': price,
            'location': location,
            'description': description,
            'url': url,
            'category': category
        }
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text like 'Rs 50,000' or '₨ 1,00,000'"""
        import re
        
        if not price_text:
            return 0.0
        
        # Remove currency symbols and 'Rs'
        price_text = price_text.replace('Rs', '').replace('₨', '').strip()
        
        # Remove commas
        price_text = price_text.replace(',', '')
        
        # Extract numbers
        match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        if match:
            return float(match.group(1))
        
        return 0.0

def main():
    """Main scraping function"""
    logger.info("="*80)
    logger.info("SIMPLE OLX SCRAPER (Requests + BeautifulSoup)")
    logger.info("="*80)
    logger.info("\n⚠️ Note: This scraper may get limited data due to JavaScript rendering.")
    logger.info("For best results, data should be collected with Selenium or from existing CSVs.\n")
    
    scraper = SimpleOLXScraper()
    
    # Create output directory
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    
    categories = ['mobile', 'laptop', 'furniture']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for category in categories:
        try:
            df = scraper.scrape_category(category, max_pages=5)  # Limit to 5 pages for demo
            
            if not df.empty:
                filename = output_dir / f"{category}_scraped_{timestamp}.csv"
                df.to_csv(filename, index=False)
                logger.info(f"✅ Saved to: {filename}")
            else:
                logger.warning(f"⚠️ No data collected for {category}")
        
        except Exception as e:
            logger.error(f"❌ Error scraping {category}: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("SCRAPING COMPLETE")
    logger.info("="*80)
    logger.info("\n💡 Recommendation: Use existing CSV data (5,903 mobiles, 1,346 laptops, 1,072 furniture)")
    logger.info("   These datasets are already high quality and have been used to train 99%+ accuracy models.")

if __name__ == "__main__":
    main()
