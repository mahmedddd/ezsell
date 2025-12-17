"""
Furniture Scraper for OLX Pakistan
Extracts: title, type, condition, price, material, color, dimensions
"""

import logging
from typing import Dict, List, Optional
import re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FurnitureScraper(BaseScraper):
    """Scraper for furniture on OLX Pakistan"""
    
    def __init__(self):
        super().__init__()
        self.category_url = f"{self.base_url}/furniture-home-decor_c387"
        
    def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse individual furniture listing"""
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
            
            # Initialize furniture data
            furniture_data = {
                'title': title,
                'price': price,
                'url': url,
                'type': self.extract_type(title, description, specs),
                'condition': self.extract_condition(specs, description),
                'material': self.extract_material(title, description, specs),
                'color': self.extract_color(title, description, specs),
                'brand': self.extract_brand(title, specs),
                'style': self.extract_style(title, description),
                'room_type': self.extract_room_type(title, description),
                'length': self.extract_dimension(description, 'length'),
                'width': self.extract_dimension(description, 'width'),
                'height': self.extract_dimension(description, 'height'),
                'seating_capacity': self.extract_seating_capacity(title, description),
                'location': self.extract_location(soup),
                'description': description[:200]
            }
            
            logger.info(f"Scraped furniture: {title[:50]}... - Rs. {price}")
            return furniture_data
            
        except Exception as e:
            logger.error(f"Error parsing listing {url}: {e}")
            return None
    
    def extract_type(self, title: str, description: str, specs: Dict) -> str:
        """Extract furniture type"""
        text = f"{title} {description}".lower()
        
        furniture_types = {
            'sofa': ['sofa', 'couch', 'settee'],
            'bed': ['bed', 'cot', 'mattress'],
            'chair': ['chair', 'dining chair', 'office chair'],
            'table': ['table', 'dining table', 'coffee table', 'study table'],
            'wardrobe': ['wardrobe', 'almirah', 'closet', 'cupboard'],
            'dresser': ['dresser', 'dressing table', 'vanity'],
            'cabinet': ['cabinet', 'showcase'],
            'desk': ['desk', 'computer table', 'workstation'],
            'shelf': ['shelf', 'bookshelf', 'rack'],
            'drawer': ['drawer', 'chest of drawers'],
            'ottoman': ['ottoman', 'footstool'],
            'tv_stand': ['tv stand', 'tv unit', 'tv cabinet'],
            'dining_set': ['dining set', 'dining room set'],
            'bedroom_set': ['bedroom set'],
            'living_room_set': ['living room set', 'lounge set']
        }
        
        for ftype, keywords in furniture_types.items():
            for keyword in keywords:
                if keyword in text:
                    return ftype.replace('_', ' ').title()
        
        return 'Other'
    
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
    
    def extract_material(self, title: str, description: str, specs: Dict) -> Optional[str]:
        """Extract primary material"""
        text = f"{title} {description}".lower()
        
        materials = {
            'wood': ['wood', 'wooden', 'teak', 'oak', 'mahogany', 'pine', 'walnut', 'sheesham'],
            'metal': ['metal', 'steel', 'iron', 'aluminum', 'aluminium'],
            'leather': ['leather', 'rexine'],
            'fabric': ['fabric', 'cloth', 'velvet', 'suede', 'linen'],
            'plastic': ['plastic', 'pvc'],
            'glass': ['glass', 'tempered glass'],
            'marble': ['marble', 'granite'],
            'mdf': ['mdf', 'particle board', 'chipboard'],
            'cane': ['cane', 'rattan', 'wicker']
        }
        
        # Check specs first
        if 'Material' in specs:
            return specs['Material']
        
        # Check description
        for material, keywords in materials.items():
            for keyword in keywords:
                if keyword in text:
                    return material.title()
        
        return None
    
    def extract_color(self, title: str, description: str, specs: Dict) -> Optional[str]:
        """Extract color"""
        if 'Color' in specs or 'Colour' in specs:
            return specs.get('Color', specs.get('Colour'))
        
        text = f"{title} {description}".lower()
        colors = [
            'Black', 'White', 'Brown', 'Beige', 'Gray', 'Grey', 'Red', 
            'Blue', 'Green', 'Yellow', 'Orange', 'Pink', 'Purple', 
            'Cream', 'Tan', 'Walnut', 'Oak', 'Cherry', 'Mahogany'
        ]
        
        for color in colors:
            if color.lower() in text:
                return color
        
        return None
    
    def extract_brand(self, title: str, specs: Dict) -> Optional[str]:
        """Extract brand if mentioned"""
        brands = [
            'IKEA', 'Habitt', 'Interwood', 'Master', 'Ideas', 
            'Khaadi Home', 'HomeSense', 'Century'
        ]
        
        if 'Brand' in specs:
            return specs['Brand']
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        return None
    
    def extract_style(self, title: str, description: str) -> Optional[str]:
        """Extract furniture style"""
        text = f"{title} {description}".lower()
        
        styles = [
            'modern', 'contemporary', 'vintage', 'antique', 'traditional',
            'classic', 'rustic', 'industrial', 'minimalist', 'luxury'
        ]
        
        for style in styles:
            if style in text:
                return style.title()
        
        return None
    
    def extract_room_type(self, title: str, description: str) -> Optional[str]:
        """Extract intended room"""
        text = f"{title} {description}".lower()
        
        rooms = {
            'Living Room': ['living room', 'lounge', 'drawing room'],
            'Bedroom': ['bedroom', 'bed room'],
            'Dining Room': ['dining room', 'dining'],
            'Office': ['office', 'study'],
            'Kitchen': ['kitchen'],
            'Bathroom': ['bathroom']
        }
        
        for room, keywords in rooms.items():
            for keyword in keywords:
                if keyword in text:
                    return room
        
        return None
    
    def extract_dimension(self, description: str, dimension_type: str) -> Optional[float]:
        """Extract dimensions (length/width/height) in feet or cm"""
        text = description.lower()
        
        # Patterns for feet
        patterns = [
            rf'{dimension_type}[:\s]+(\d+\.?\d*)\s*(?:ft|feet|foot)',
            rf'(\d+\.?\d*)\s*(?:ft|feet|foot)\s*{dimension_type}',
            rf'{dimension_type}[:\s]+(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                dim = float(match.group(1))
                if 0.5 <= dim <= 30:  # Reasonable range in feet
                    return dim
        
        return None
    
    def extract_seating_capacity(self, title: str, description: str) -> Optional[int]:
        """Extract seating capacity for sofas/dining sets"""
        text = f"{title} {description}".lower()
        
        patterns = [
            r'(\d+)\s*seater',
            r'seats\s*(\d+)',
            r'(\d+)\s*person'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                capacity = int(match.group(1))
                if 1 <= capacity <= 20:
                    return capacity
        
        return None
    
    def extract_location(self, soup) -> str:
        """Extract listing location"""
        loc_elem = soup.find('span', attrs={'data-aut-id': 'item-location'})
        if not loc_elem:
            loc_elem = soup.find('span', class_=re.compile(r'location'))
        return self.clean_text(loc_elem.get_text()) if loc_elem else 'Unknown'
    
    def scrape(self, max_pages: int = 10, max_listings: int = 500) -> List[Dict]:
        """Scrape furniture listings from OLX Pakistan"""
        logger.info(f"Starting furniture scraping from {self.category_url}")
        
        listing_urls = self.extract_listing_urls(self.category_url, max_pages)
        listing_urls = listing_urls[:max_listings]
        
        furniture_data = []
        for i, url in enumerate(listing_urls, 1):
            logger.info(f"Scraping listing {i}/{len(listing_urls)}")
            
            data = self.parse_listing(url)
            if data:
                furniture_data.append(data)
            
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(listing_urls)} - Collected: {len(furniture_data)}")
        
        logger.info(f"Furniture scraping complete! Collected {len(furniture_data)} listings")
        return furniture_data
