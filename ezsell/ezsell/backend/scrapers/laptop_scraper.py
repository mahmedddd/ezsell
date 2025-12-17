"""
Laptop Scraper for OLX Pakistan
Extracts: title, brand, condition, price, processor, ram, storage, gpu, screen_size
"""

import logging
from typing import Dict, List, Optional
import re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class LaptopScraper(BaseScraper):
    """Scraper for laptops on OLX Pakistan"""
    
    def __init__(self):
        super().__init__()
        self.category_url = f"{self.base_url}/computers-accessories/laptops_c1651"
        
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse individual laptop listing"""
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
            
            # Extract description
            desc_elem = soup.find('div', attrs={'data-aut-id': 'itemDescriptionContent'})
            description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
            
            # Extract specifications
            specs = self.extract_specs(soup)
            
            # Initialize laptop data
            laptop_data = {
                'title': title,
                'price': price,
                'url': url,
                'brand': self.extract_brand(title, specs),
                'condition': self.extract_condition(specs, description),
                'processor': self.extract_processor(title, description, specs),
                'processor_type': self.extract_processor_type(title, description),
                'generation': self.extract_generation(title, description),
                'ram': self.extract_ram(title, description, specs),
                'storage': self.extract_storage(title, description, specs),
                'storage_type': self.extract_storage_type(title, description),
                'gpu': self.extract_gpu(title, description, specs),
                'screen_size': self.extract_screen_size(title, description, specs),
                'model': self.extract_model(title, specs),
                'location': self.extract_location(soup),
                'description': description[:200]
            }
            
            logger.info(f"Scraped laptop: {title[:50]}... - Rs. {price}")
            return laptop_data
            
        except Exception as e:
            logger.error(f"Error parsing listing {url}: {e}")
            return None
    
    def extract_brand(self, title: str, specs: Dict) -> str:
        """Extract laptop brand"""
        brands = [
            'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Apple', 'MacBook', 
            'Microsoft', 'Surface', 'MSI', 'Razer', 'Alienware', 'Samsung',
            'Toshiba', 'Sony', 'LG', 'Huawei', 'Xiaomi', 'Compaq'
        ]
        
        if 'Brand' in specs or 'Make' in specs:
            return specs.get('Brand', specs.get('Make', 'Unknown'))
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        return 'Unknown'
    
    def extract_condition(self, specs: Dict, description: str) -> str:
        """Extract condition"""
        condition_keys = ['Condition', 'Type']
        for key in condition_keys:
            if key in specs:
                return specs[key]
        
        desc_lower = description.lower()
        if 'brand new' in desc_lower or 'new' in desc_lower[:50]:
            return 'New'
        elif 'used' in desc_lower[:50] or 'second hand' in desc_lower:
            return 'Used'
        
        return 'Used'
    
    def extract_processor(self, title: str, description: str, specs: Dict) -> Optional[str]:
        """Extract processor model"""
        text = f"{title} {description}".lower()
        
        # Intel patterns
        intel_patterns = [
            r'(core\s*i[3579]\s*-?\s*\d{4,5}[a-z]*)',
            r'(i[3579]\s*-?\s*\d{4,5}[a-z]*)',
            r'(pentium|celeron|xeon)\s*[a-z]?\d*'
        ]
        
        for pattern in intel_patterns:
            match = re.search(pattern, text)
            if match:
                return self.clean_text(match.group(1))
        
        # AMD patterns
        amd_patterns = [
            r'(ryzen\s*[3579]\s*\d{4}[a-z]*)',
            r'(athlon|a[4-9]|fx)\s*-?\s*\d*'
        ]
        
        for pattern in amd_patterns:
            match = re.search(pattern, text)
            if match:
                return self.clean_text(match.group(1))
        
        return None
    
    def extract_processor_type(self, title: str, description: str) -> Optional[str]:
        """Extract processor brand (Intel/AMD/Apple)"""
        text = f"{title} {description}".lower()
        
        if 'intel' in text or 'core i' in text or 'pentium' in text or 'celeron' in text:
            return 'Intel'
        elif 'amd' in text or 'ryzen' in text or 'athlon' in text:
            return 'AMD'
        elif 'm1' in text or 'm2' in text or 'm3' in text or 'apple silicon' in text:
            return 'Apple'
        
        return None
    
    def extract_generation(self, title: str, description: str) -> Optional[str]:
        """Extract processor generation"""
        text = f"{title} {description}".lower()
        
        gen_patterns = [
            r'(\d{1,2})(th|st|nd|rd)?\s*gen',
            r'gen\s*(\d{1,2})',
            r'generation\s*(\d{1,2})'
        ]
        
        for pattern in gen_patterns:
            match = re.search(pattern, text)
            if match:
                gen = match.group(1)
                return f"{gen}th Gen"
        
        # Infer from processor model (Intel)
        processor_match = re.search(r'i[3579]\s*-?\s*(\d)(\d{3})', text)
        if processor_match:
            gen = processor_match.group(1)
            if gen.isdigit():
                return f"{gen}th Gen"
        
        return None
    
    def extract_ram(self, title: str, description: str, specs: Dict) -> Optional[int]:
        """Extract RAM in GB"""
        text = f"{title} {description}".lower()
        
        ram_patterns = [
            r'(\d+)\s*gb\s*ram',
            r'ram\s*(\d+)\s*gb',
            r'(\d+)\s*gb\s*ddr'
        ]
        
        for pattern in ram_patterns:
            match = re.search(pattern, text)
            if match:
                ram = int(match.group(1))
                if 2 <= ram <= 128:
                    return ram
        
        return None
    
    def extract_storage(self, title: str, description: str, specs: Dict) -> Optional[int]:
        """Extract storage in GB"""
        text = f"{title} {description}".lower()
        
        storage_patterns = [
            r'(\d+)\s*gb\s*(?:ssd|hdd|nvme|storage)',
            r'(\d+)\s*tb\s*(?:ssd|hdd|nvme)',
            r'(?:ssd|hdd|nvme)\s*(\d+)\s*(?:gb|tb)'
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, text)
            if match:
                storage = int(match.group(1))
                # Convert TB to GB if needed
                if 'tb' in match.group(0):
                    storage *= 1024
                if 64 <= storage <= 4096:
                    return storage
        
        return None
    
    def extract_storage_type(self, title: str, description: str) -> Optional[str]:
        """Extract storage type (SSD/HDD/NVMe)"""
        text = f"{title} {description}".lower()
        
        if 'nvme' in text or 'nvme ssd' in text:
            return 'NVMe SSD'
        elif 'ssd' in text:
            return 'SSD'
        elif 'hdd' in text or 'hard disk' in text or 'hard drive' in text:
            return 'HDD'
        
        return None
    
    def extract_gpu(self, title: str, description: str, specs: Dict) -> Optional[str]:
        """Extract GPU/Graphics card"""
        text = f"{title} {description}".lower()
        
        # NVIDIA patterns
        nvidia_patterns = [
            r'(gtx\s*\d{3,4}\s*ti?)',
            r'(rtx\s*\d{3,4}\s*ti?)',
            r'(geforce\s*(?:gtx|rtx)?\s*\d{3,4})',
            r'(mx\s*\d{3})'
        ]
        
        for pattern in nvidia_patterns:
            match = re.search(pattern, text)
            if match:
                return f"NVIDIA {match.group(1).upper()}"
        
        # AMD patterns
        amd_patterns = [
            r'(radeon\s*(?:rx)?\s*\d{3,4})',
            r'(vega\s*\d+)',
        ]
        
        for pattern in amd_patterns:
            match = re.search(pattern, text)
            if match:
                return f"AMD {match.group(1).upper()}"
        
        # Integrated graphics
        if 'intel uhd' in text or 'intel hd' in text:
            return 'Intel Integrated'
        elif 'amd radeon graphics' in text or 'radeon graphics' in text:
            return 'AMD Integrated'
        
        return None
    
    def extract_screen_size(self, title: str, description: str, specs: Dict) -> Optional[float]:
        """Extract screen size in inches"""
        text = f"{title} {description}".lower()
        
        screen_patterns = [
            r'(\d+\.?\d*)\s*(?:inch|"|\')',
            r'(\d+\.?\d*)\s*screen'
        ]
        
        for pattern in screen_patterns:
            match = re.search(pattern, text)
            if match:
                size = float(match.group(1))
                if 10.0 <= size <= 21.0:
                    return size
        
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
        """Scrape laptop listings from OLX Pakistan"""
        logger.info(f"Starting laptop scraping from {self.category_url}")
        
        listing_urls = self.extract_listing_urls(self.category_url, max_pages)
        listing_urls = listing_urls[:max_listings]
        
        laptop_data = []
        for i, url in enumerate(listing_urls, 1):
            logger.info(f"Scraping listing {i}/{len(listing_urls)}")
            
            data = self.parse_listing(url)
            if data:
                laptop_data.append(data)
            
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(listing_urls)} - Collected: {len(laptop_data)}")
        
        logger.info(f"Laptop scraping complete! Collected {len(laptop_data)} listings")
        return laptop_data
