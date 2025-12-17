"""
Base scraper class with common functionality for OLX Pakistan
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for OLX scrapers with common functionality"""
    
    def __init__(self, base_url: str = "https://www.olx.com.pk"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with retry logic"""
        for attempt in range(max_retries):
            try:
                # Random delay to avoid being blocked
                time.sleep(random.uniform(2, 5))
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
                time.sleep(random.uniform(5, 10))
        
        return None
    
    def clean_price(self, price_text: str) -> Optional[int]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove 'Rs', commas, and whitespace
        price_text = re.sub(r'[Rs,\s]', '', price_text)
        
        # Extract numbers
        numbers = re.findall(r'\d+', price_text)
        if numbers:
            return int(''.join(numbers))
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def extract_listing_urls(self, category_url: str, max_pages: int = 5) -> List[str]:
        """Extract individual listing URLs from category pages"""
        listing_urls = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{category_url}?page={page}"
            logger.info(f"Fetching page {page}: {page_url}")
            
            soup = self.get_page(page_url)
            if not soup:
                break
            
            # OLX uses different selectors, try multiple patterns
            links = soup.find_all('a', href=re.compile(r'/item/'))
            
            for link in links:
                href = link.get('href')
                if href and '/item/' in href:
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    if full_url not in listing_urls:
                        listing_urls.append(full_url)
            
            logger.info(f"Found {len(listing_urls)} listings so far")
            
            # Check if there's a next page
            if not soup.find('a', {'data-aut-id': 'btnLoadMore'}):
                break
        
        logger.info(f"Total listings found: {len(listing_urls)}")
        return listing_urls
    
    @abstractmethod
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse individual listing page - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def scrape(self, max_pages: int = 5) -> List[Dict]:
        """Main scraping method - must be implemented by subclasses"""
        pass
    
    def extract_specs(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract specifications from OLX listing page"""
        specs = {}
        
        # Try to find spec sections
        spec_sections = soup.find_all('div', class_=re.compile(r'_[0-9a-z]+'))
        
        for section in spec_sections:
            # Look for key-value pairs
            labels = section.find_all(['span', 'div'], class_=re.compile(r'label|key'))
            values = section.find_all(['span', 'div'], class_=re.compile(r'value'))
            
            for label, value in zip(labels, values):
                key = self.clean_text(label.get_text())
                val = self.clean_text(value.get_text())
                if key and val:
                    specs[key] = val
        
        # Also try data attributes approach
        spec_items = soup.find_all(attrs={'data-aut-id': re.compile(r'itemParam')})
        for item in spec_items:
            text = item.get_text()
            if ':' in text:
                key, val = text.split(':', 1)
                specs[self.clean_text(key)] = self.clean_text(val)
        
        return specs
