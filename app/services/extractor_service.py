"""
Data extraction service for parsing product information from web pages
"""

import re
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .intelligent_price_extractor import intelligent_price_extractor


class ExtractorService:
    """Service for extracting product data from web pages"""
    
    # Site-specific selector rules for better extraction
    SITE_SPECIFIC_RULES = {
        "amazon": {
            "title": [
                '#productTitle',
                '.product-title',
                '[data-automation-id="product-title"]',
                'h1.a-size-large',
                'h1 span'
            ],
            "price": [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '.a-price-range .a-price .a-offscreen',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price.a-text-price.a-size-medium.a-color-base',
                '.a-price-current',
                '[data-testid="price"] .a-price .a-offscreen'
            ],
            "description": [
                '#feature-bullets ul',
                '.a-unordered-list.a-vertical',
                '[data-feature-name="featurebullets"]',
                '.product-facts-detail'
            ]
        },
        "johnlewis": {
            "title": [
                '.pdp-product-name',
                '.product-title',
                'h1[class*="title"]'
            ],
            "description": [
                '.pdp-product-description',
                '.product-description .c-product-details__description',
                '.c-product-details__description',
                '.product-information',
                '.product-details .content'
            ]
        },
        "currys": {
            "title": [
                '.pdp-product-name',
                '.product-title',
                'h1'
            ],
            "description": [
                '.product-description',
                '.description-content',
                '.product-info'
            ]
        },
        "smythstoys": {
            "title": [
                '.product-name h1',
                '.product-title',
                '.pdp-product-name'
            ],
            "price": [
                '.price-current',
                '.current-price',
                '.product-price .price',
                '[data-testid="price"]'
            ],
            "description": [
                '.product-description',
                '.product-overview',
                '.description-content'
            ]
        },
        "thetoyshop": {
            "title": [
                '.product-name',
                '.product-title',
                'h1'
            ],
            "price": [
                '.price-current',
                '.current-price', 
                '.product-price',
                '[data-price]',
                '.price .value'
            ],
            "description": [
                '.product-description',
                '.product-details',
                '.description'
            ]
        }
    }
    
    # Smart selectors for different product data (fallback)
    EXTRACTION_RULES = {
        "title": [
            'h1[class*="title"]',
            'h1[id*="title"]',
            '[data-testid*="title"]',
            '.product-title',
            '.product-name', 
            '[class*="product-title"]',
            '[class*="product-name"]',
            '[itemprop="name"]',
            'h1',
            'title'
        ],
        "price": [
            '[class*="price"]:not([class*="original"]):not([class*="was"]):not([class*="msrp"])',
            '[data-testid*="price"]',
            '[class*="current-price"]',
            '[class*="sale-price"]',
            '.price-current',
            '.price-now',
            '[itemprop="price"]',
            '.price:not(.price-original)',
            '[class*="cost"]'
        ],
        "description": [
            '[class*="description"]:not([class*="short"]):not([class*="brief"])',
            '[data-testid*="description"]', 
            '.product-description',
            '.product-details',
            '[class*="product-description"]',
            '[itemprop="description"]',
            '.description',
            '.details',
            'meta[name="description"]'
        ],
        "image": [
            '.product-image img',
            '[class*="hero"] img',
            '.main-image img', 
            '.primary-image img',
            '[class*="product-image"] img',
            'img[alt*="product"]',
            '[data-testid*="image"] img',
            '.gallery img:first-of-type',
            'img:first-of-type'
        ]
    }
    
    # Currency patterns for detection
    CURRENCY_PATTERNS = {
        "symbols": {
            "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
            "₹": "INR", "C$": "CAD", "A$": "AUD", "kr": "SEK", "₽": "RUB"
        },
        "codes": re.compile(r'\b(USD|EUR|GBP|JPY|CAD|AUD|SEK|NOK|DKK|CHF|PLN|CZK|HUF|RUB|INR|CNY|KRW|BRL|MXN|ZAR)\b', re.IGNORECASE),
        "domain_mapping": {
            ".com": "USD", ".co.uk": "GBP", ".de": "EUR", ".fr": "EUR",
            ".it": "EUR", ".es": "EUR", ".ca": "CAD", ".au": "AUD",
            ".jp": "JPY", ".in": "INR", ".br": "BRL", ".mx": "MXN"
        }
    }
    
    def __init__(self):
        pass
    
    def _get_site_type(self, url: str) -> Optional[str]:
        """Detect site type for specific optimizations"""
        domain = urlparse(url).netloc.lower()
        
        if 'amazon' in domain:
            return 'amazon'
        elif 'johnlewis' in domain:
            return 'johnlewis'
        elif 'currys' in domain:
            return 'currys'
        elif 'smythstoys' in domain:
            return 'smythstoys'
        elif 'thetoyshop' in domain:
            return 'thetoyshop'
        
        return None
    
    def _is_valid_description(self, text: str) -> bool:
        """Check if description text is valid product information"""
        if not text or len(text.strip()) < 20:
            return False
        
        # Filter out common non-description content
        invalid_patterns = [
            r'credit subject to',
            r'\d+\s*years?\s*\+',  # Age restrictions
            r'uk residents',
            r't&cs? apply',
            r'terms and conditions',
            r'description.*description',  # UI element repetition
            r'^(off|selected|on)$',
            r'click to',
            r'add to basket',
            r'sign in'
        ]
        
        text_lower = text.lower()
        for pattern in invalid_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Check for actual product information indicators
        product_indicators = [
            r'\b(features?|specification|dimension|material|color|colour|size|weight)\b',
            r'\b(perfect for|ideal for|designed for|suitable for)\b',
            r'\b(includes?|comes? with|equipped with)\b'
        ]
        
        for indicator in product_indicators:
            if re.search(indicator, text_lower):
                return True
        
        # If it's reasonably long and doesn't match invalid patterns, it's probably valid
        return len(text) > 50
    
    async def extract_product_data(self, page, url: str) -> Dict[str, Any]:
        """Extract product data from a page"""
        try:
            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=5000)
        except:
            # Continue if networkidle timeout
            pass
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract data using smart selectors
        title = self._extract_title(soup, url)
        price = self._extract_price(soup, url) 
        description = self._extract_description(soup, url)
        image = self._extract_image(soup, url)
        currency = self._detect_currency(price, url)
        
        # Clean up price
        if price:
            price = self._clean_price(price)
        
        return {
            "title": title,
            "price": price, 
            "currency": currency,
            "description": description,
            "image": image,
            "url": url
        }
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract product title with site-specific optimizations"""
        site_type = self._get_site_type(url)
        
        # Try site-specific selectors first
        if site_type and site_type in self.SITE_SPECIFIC_RULES:
            selectors = self.SITE_SPECIFIC_RULES[site_type].get('title', [])
            for selector in selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if text and len(text.strip()) > 5:
                            # Clean title text
                            cleaned = re.sub(r'\s+', ' ', text).strip()
                            return cleaned[:200]
                except Exception:
                    continue
        
        # Fallback to generic selectors
        for selector in self.EXTRACTION_RULES["title"]:
            try:
                element = soup.select_one(selector)
                if element:
                    if selector == 'title':
                        text = element.get_text(strip=True)
                        # Extract product name from page title
                        if ' - ' in text:
                            text = text.split(' - ')[0].strip()
                        elif ' | ' in text:
                            text = text.split(' | ')[0].strip()
                    elif element.name == 'meta':
                        text = element.get('content', '').strip()
                    else:
                        text = element.get_text(strip=True)
                    
                    if text and len(text.strip()) > 5:
                        # Clean and validate title
                        cleaned = re.sub(r'\s+', ' ', text).strip()
                        # Skip obviously wrong titles
                        if not re.match(r'^(video|image|hero)', cleaned.lower()):
                            return cleaned[:200]
            except Exception:
                continue
        return None
    
    def _extract_price(self, soup: BeautifulSoup, url: str = "") -> Optional[str]:
        """Extract product price using intelligent extraction with scoring"""
        # Use the new intelligent price extractor
        price = intelligent_price_extractor.extract_price(soup, url)
        if price:
            return price
        
        # Fallback to legacy method if intelligent extraction fails
        return self._extract_price_legacy(soup, url)
    
    def _extract_price_legacy(self, soup: BeautifulSoup, url: str = "") -> Optional[str]:
        """Legacy price extraction method as fallback"""
        site_type = self._get_site_type(url) if url else None
        
        # Try site-specific selectors first
        if site_type and site_type in self.SITE_SPECIFIC_RULES:
            price_selectors = self.SITE_SPECIFIC_RULES[site_type].get('price', [])
            for selector in price_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        # Check if text contains price-like patterns
                        if text and re.search(r'[\d\$€£¥₹]', text):
                            return text
                except Exception:
                    continue
        
        # Fallback to generic selectors
        for selector in self.EXTRACTION_RULES["price"]:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    # Check if text contains price-like patterns
                    if text and re.search(r'[\d\$€£¥₹]', text):
                        return text
            except Exception:
                continue
        return None
    
    def _extract_description(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract product description with enhanced filtering"""
        site_type = self._get_site_type(url)
        
        # Try site-specific selectors first
        if site_type and site_type in self.SITE_SPECIFIC_RULES:
            selectors = self.SITE_SPECIFIC_RULES[site_type].get('description', [])
            for selector in selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        if element.name == 'ul':
                            # For Amazon-style bullet points
                            items = element.find_all('li')
                            if items:
                                text = '. '.join([item.get_text(strip=True) for item in items[:5]])
                            else:
                                text = element.get_text(strip=True)
                        else:
                            text = element.get_text(strip=True)
                        
                        # Clean whitespace
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        if self._is_valid_description(text):
                            return text[:800] + ('...' if len(text) > 800 else '')
                except Exception:
                    continue
        
        # Fallback to generic selectors with validation
        for selector in self.EXTRACTION_RULES["description"]:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        text = element.get('content', '').strip()
                    else:
                        text = element.get_text(strip=True)
                    
                    # Clean whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if self._is_valid_description(text):
                        return text[:800] + ('...' if len(text) > 800 else '')
            except Exception:
                continue
        return None
    
    def _extract_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract product image URL"""
        for selector in self.EXTRACTION_RULES["image"]:
            try:
                element = soup.select_one(selector)
                if element:
                    img_url = (element.get('src') or 
                              element.get('data-src') or 
                              element.get('data-lazy'))
                    
                    if img_url:
                        # Convert relative URLs to absolute
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif not img_url.startswith('http'):
                            img_url = urljoin(base_url, img_url)
                        return img_url
            except Exception:
                continue
        return None
    
    def _detect_currency(self, price_text: Optional[str], url: str) -> str:
        """Detect currency from price text and URL"""
        if not price_text:
            return self._currency_from_domain(url)
        
        # Method 1: Look for currency codes
        code_match = self.CURRENCY_PATTERNS["codes"].search(price_text)
        if code_match:
            return code_match.group(1).upper()
        
        # Method 2: Look for currency symbols
        for symbol, currency in self.CURRENCY_PATTERNS["symbols"].items():
            if symbol in price_text:
                return currency
        
        # Method 3: Infer from domain
        return self._currency_from_domain(url)
    
    def _currency_from_domain(self, url: str) -> str:
        """Detect currency from domain TLD"""
        try:
            domain = urlparse(url).netloc.lower()
            for tld, currency in self.CURRENCY_PATTERNS["domain_mapping"].items():
                if domain.endswith(tld):
                    return currency
        except Exception:
            pass
        return "USD"  # Default fallback
    
    def _clean_price(self, price_text: str) -> str:
        """Clean and normalize price text"""
        if not price_text:
            return price_text
            
        # Remove common non-price words
        cleaned = re.sub(r'\s*(from|starting|up to|as low as|only|just)\s*', '', price_text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*(per|each|ea\.)\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # Extract price pattern
        price_match = re.search(r'[\$€£¥₹]?[\d,]+\.?\d*', cleaned)
        return price_match.group(0) if price_match else cleaned