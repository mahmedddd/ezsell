"""
Mobile Phone Scraper for OLX Pakistan
Extracts: title, brand, condition, price, RAM, storage, battery, screen_size, camera
"""

import logging
from typing import Dict, List, Optional
import re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MobileScraper(BaseScraper):
    """Scraper for mobile phones on OLX Pakistan"""
    
    def __init__(self):
        super().__init__()
        self.category_url = f"{self.base_url}/mobile-phones_c1453"
        
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse individual mobile listing"""
        soup = self.get_page(url)
        if not soup:
            return None
        
        try:
            # Extract title
            title_elem = soup.find('h1', attrs={'data-aut-id': 'itemTitle'})
            if not title_elem:
                title_elem = soup.find('h1')
            title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown"
            
            # Extract price
            price_elem = soup.find('span', attrs={'data-aut-id': 'itemPrice'})
            if not price_elem:
                price_elem = soup.find('span', class_=re.compile(r'price'))
            price = self.clean_price(price_elem.get_text()) if price_elem else None
            
            # Skip if no price
            if not price:
                return None
            
            # Extract description for additional info
            desc_elem = soup.find('div', attrs={'data-aut-id': 'itemDescriptionContent'})
            description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
            
            # Extract specifications
            specs = self.extract_specs(soup)
            
            # Initialize mobile data
            mobile_data = {
                'title': title,
                'price': price,
                'url': url,
                'brand': self.extract_brand(title, specs),
                'condition': self.extract_condition(specs, description),
                'ram': self.extract_ram(title, description, specs),
                'storage': self.extract_storage(title, description, specs),
                'battery': self.extract_battery(description, specs),
                'screen_size': self.extract_screen_size(description, specs),
                'camera': self.extract_camera(description, specs),
                'color': self.extract_color(specs, description),
                'model': self.extract_model(title, specs),
                'location': self.extract_location(soup),
                'description': description[:200]  # First 200 chars
            }
            
            logger.info(f"Scraped mobile: {title[:50]}... - Rs. {price}")
            return mobile_data
            
        except Exception as e:
            logger.error(f"Error parsing listing {url}: {e}")
            return None
    
    def extract_brand(self, title: str, specs: Dict) -> str:
        """Extract mobile brand"""
        brands = [
            'Samsung', 'Apple', 'iPhone', 'Xiaomi', 'Oppo', 'Vivo', 'Realme', 
            'OnePlus', 'Huawei', 'Honor', 'Nokia', 'Motorola', 'Sony', 'LG',
            'Infinix', 'Tecno', 'Itel', 'Google', 'Pixel', 'Redmi', 'Poco'
        ]
        
        # Check specs first
        if 'Brand' in specs or 'Make' in specs:
            return specs.get('Brand', specs.get('Make', 'Unknown'))
        
        # Check title
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        return 'Unknown'
    
    def extract_condition(self, specs: Dict, description: str) -> str:
        """Extract condition (New/Used)"""
        condition_keys = ['Condition', 'Type']
        for key in condition_keys:
            if key in specs:
                return specs[key]
        
        # Check description
        desc_lower = description.lower()
        if 'brand new' in desc_lower or 'new' in desc_lower[:50]:
            return 'New'
        elif 'used' in desc_lower[:50]:
            return 'Used'
        
        return 'Used'  # Default to used
    
    def extract_ram(self, title: str, description: str, specs: Dict) -> Optional[int]:
        """Extract RAM in GB"""
        text = f"{title} {description}"
        
        # Look for patterns like "8GB RAM", "8 GB", "8gb"
        ram_patterns = [
            r'(\d+)\s*gb\s*ram',
            r'ram\s*(\d+)\s*gb',
            r'(\d+)\s*gb\s*memory'
        ]
        
        for pattern in ram_patterns:
            match = re.search(pattern, text.lower())
            if match:
                ram = int(match.group(1))
                if 1 <= ram <= 32:  # Reasonable range
                    return ram
        
        return None
    
    def extract_storage(self, title: str, description: str, specs: Dict) -> Optional[int]:
        """Extract storage in GB"""
        text = f"{title} {description}"
        
        # Look for patterns like "128GB", "256 GB", "1TB"
        storage_patterns = [
            r'(\d+)\s*gb\s*(?:storage|rom|internal)',
            r'(\d+)\s*gb(?!\s*ram)',
            r'(\d+)\s*tb'
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, text.lower())
            if match:
                storage = int(match.group(1))
                # Convert TB to GB
                if 'tb' in pattern:
                    storage *= 1024
                if 8 <= storage <= 2048:  # Reasonable range
                    return storage
        
        return None
    
    def extract_battery(self, description: str, specs: Dict) -> Optional[int]:
        """Extract battery capacity in mAh"""
        text = description.lower()
        
        # Look for patterns like "5000mAh", "5000 mAh"
        battery_patterns = [
            r'(\d+)\s*mah',
            r'battery[:\s]+(\d+)',
        ]
        
        for pattern in battery_patterns:
            match = re.search(pattern, text)
            if match:
                battery = int(match.group(1))
                if 1000 <= battery <= 10000:  # Reasonable range
                    return battery
        
        return None
    
    def extract_screen_size(self, description: str, specs: Dict) -> Optional[float]:
        """Extract screen size in inches"""
        text = description.lower()
        
        # Look for patterns like '6.5"', '6.5 inch', '6.5"'
        screen_patterns = [
            r'(\d+\.?\d*)\s*(?:inch|"|\')',
            r'screen[:\s]+(\d+\.?\d*)'
        ]
        
        for pattern in screen_patterns:
            match = re.search(pattern, text)
            if match:
                size = float(match.group(1))
                if 3.0 <= size <= 8.0:  # Reasonable range
                    return size
        
        return None
    
    def extract_camera(self, description: str, specs: Dict) -> Optional[int]:
        """Extract main camera megapixels"""
        text = description.lower()
        
        # Look for patterns like "48MP", "48 MP camera", "48 megapixel"
        camera_patterns = [
            r'(\d+)\s*mp',
            r'(\d+)\s*megapixel',
            r'camera[:\s]+(\d+)'
        ]
        
        for pattern in camera_patterns:
            match = re.search(pattern, text)
            if match:
                mp = int(match.group(1))
                if 2 <= mp <= 200:  # Reasonable range
                    return mp
        
        return None
    
    def extract_color(self, specs: Dict, description: str) -> Optional[str]:
        """Extract color"""
        if 'Color' in specs or 'Colour' in specs:
            return specs.get('Color', specs.get('Colour'))
        
        colors = ['Black', 'White', 'Blue', 'Red', 'Green', 'Gold', 'Silver', 'Gray', 'Purple', 'Pink']
        desc_lower = description.lower()
        for color in colors:
            if color.lower() in desc_lower:
                return color
        
        return None
    
    def extract_model(self, title: str, specs: Dict) -> str:
        """Extract model name"""
        if 'Model' in specs:
            return specs['Model']
        return title
    
    def extract_location(self, soup) -> str:
        """Extract listing location"""
        loc_elem = soup.find('span', attrs={'data-aut-id': 'item-location'})
        if not loc_elem:
            loc_elem = soup.find('span', class_=re.compile(r'location'))
        return self.clean_text(loc_elem.get_text()) if loc_elem else 'Unknown'
    
    def scrape(self, max_pages: int = 10, max_listings: int = 500) -> List[Dict]:
        """Scrape mobile listings from OLX Pakistan"""
        logger.info(f"Starting mobile scraping from {self.category_url}")
        
        # Get listing URLs
        listing_urls = self.extract_listing_urls(self.category_url, max_pages)
        
        # Limit listings
        listing_urls = listing_urls[:max_listings]
        
        # Parse each listing
        mobile_data = []
        for i, url in enumerate(listing_urls, 1):
            logger.info(f"Scraping listing {i}/{len(listing_urls)}")
            
            data = self.parse_listing(url)
            if data:
                mobile_data.append(data)
            
            # Progress update every 10 listings
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(listing_urls)} - Collected: {len(mobile_data)}")
        
        logger.info(f"Mobile scraping complete! Collected {len(mobile_data)} listings")
        return mobile_data
