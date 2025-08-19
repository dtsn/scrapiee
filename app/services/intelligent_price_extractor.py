"""
Intelligent Price Extraction Service
Advanced price extraction using currency pattern matching and element scoring
Based on JavaScript price hare algorithm for improved accuracy
"""

import re
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse


class PriceCandidate:
    """Price candidate with scoring information"""
    
    def __init__(self, element: Tag, price_match: str, index: int = 0):
        self.element = element
        self.price_match = price_match
        self.index = index
        self.score = 0.0
        self.text = element.get_text(strip=True) if element else ""


class IntelligentPriceExtractor:
    """
    Intelligent price extraction using currency pattern matching and element scoring
    Implements multi-layered approach: OpenGraph -> Whitelist -> Pattern Matching + Scoring
    """
    
    # Comprehensive currency pattern matching (expanded from your JS code)
    PRICE_PATTERN = re.compile(
        r'(?:'
        r'\$|USD|'                      # Dollar symbols
        r'&pound;|£|&#163;|&#xa3;|\u00A3|'  # Pound symbols  
        r'&yen;|\uFFE5|&#165;|&#xa5;|\u00A5|'  # Yen symbols
        r'EUR|&euro;|€|&#8364;|&#x20ac;|'   # Euro symbols
        r'&\#8377;|\u20B9|₹|'           # Rupee symbols
        r'CAD|C\$|AUD|A\$|'             # Other dollar variants
        r'CHF|SEK|NOK|DKK|PLN|CZK|'     # European currencies
        r'RUB|₽|CNY|¥|KRW|₩|'          # Asian currencies
        r'BRL|R\$|MXN|ZAR|R'            # Other currencies
        r')\s*'
        r'(\d{1,3}(?:[,.]?\d{3})*(?:\.\d{2})?)',  # Number with comma/decimal handling
        re.IGNORECASE
    )
    
    # Pattern to extract just the numeric value
    NUMERIC_PATTERN = re.compile(r'(?:\d*\.)?\d+(?:[,]\d{3})*(?:\.\d{2})?')
    
    # Site-specific whitelist with domain overrides for problematic sites
    SITE_WHITELIST = {
        'amazon': {
            'domain': r'amazon\.',
            'selectors': [
                '.a-price-whole',
                '.a-price .a-offscreen', 
                '.a-price-current',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price-range .a-price .a-offscreen'
            ],
            'use_intelligent': False  # Skip intelligent extraction for Amazon
        },
        'johnlewis': {
            'domain': r'johnlewis\.com',
            'selectors': [
                '.price',
                '.current-price',
                '.price-current'
            ],
            'use_intelligent': True
        },
        'argos': {
            'domain': r'argos\.co\.uk',
            'selectors': [
                '.price',
                '.current-price',
                '[data-test="product-price"]'
            ],
            'use_intelligent': True
        },
        'halfords': {
            'domain': r'halfords\.com',
            'selectors': [
                '.price-current',
                '.current-price',
                '.price',
                '[data-testid="price"]',
                '.product-price'
            ],
            'use_intelligent': False  # Skip intelligent extraction for Halfords
        },
        'smythstoys': {
            'domain': r'smythstoys\.com',
            'selectors': [
                '.price-current',
                '.current-price',
                '.product-price .price',
                '[data-testid="price"]'
            ],
            'use_intelligent': False
        },
        'thetoyshop': {
            'domain': r'thetoyshop\.com',
            'selectors': [
                '.price-current',
                '.current-price', 
                '.product-price',
                '[data-price]',
                '.price .value'
            ],
            'use_intelligent': True  # Intelligent works well here
        }
    }
    
    def __init__(self):
        pass
    
    def _get_site_config(self, url: str) -> Optional[Dict]:
        """Get site-specific configuration for a URL"""
        if not url:
            return None
            
        domain = urlparse(url).netloc.lower()
        
        for site_config in self.SITE_WHITELIST.values():
            if re.search(site_config['domain'], domain, re.IGNORECASE):
                return site_config
        
        return None
    
    def extract_price(self, soup: BeautifulSoup, url: str = "") -> Optional[str]:
        """
        Extract price using multi-layered intelligent approach
        1. OpenGraph meta tags
        2. Site-specific whitelist (with override control)
        3. Pattern matching with scoring (if enabled for domain)
        """
        
        # Check if this domain has specific configuration
        site_config = self._get_site_config(url) if url else None
        
        # Step 1: Try OpenGraph meta tags first
        price = self._extract_from_opengraph(soup)
        if price:
            return self._clean_price(price)
        
        # Step 2: Try site-specific whitelist
        if url:
            price = self._extract_from_whitelist(soup, url)
            if price:
                return self._clean_price(price)
        
        # Step 3: Intelligent pattern matching with scoring (only if enabled)
        if not site_config or site_config.get('use_intelligent', True):
            price = self._extract_with_scoring(soup)
            if price:
                return self._clean_price(price)
        
        return None
    
    def _extract_from_opengraph(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price from OpenGraph meta tags"""
        meta_tags = soup.find_all('meta')
        
        for tag in meta_tags:
            property_attr = tag.get('property') or tag.get('name')
            if not property_attr:
                continue
            
            content = tag.get('content') or tag.get('value')
            if not content:
                continue
            
            # Check for price-related OpenGraph properties
            if re.search(r':price$|:price:amount$', property_attr, re.IGNORECASE):
                return content
            
            # Check for data1/data2 with price patterns
            if re.search(r':data[12]$', property_attr, re.IGNORECASE):
                if self.PRICE_PATTERN.search(content):
                    return content
        
        return None
    
    def _extract_from_whitelist(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract price using site-specific whitelist"""
        domain = urlparse(url).netloc.lower()
        
        for site_config in self.SITE_WHITELIST.values():
            if re.search(site_config['domain'], domain, re.IGNORECASE):
                for selector in site_config['selectors']:
                    try:
                        elements = soup.select(selector)
                        for element in elements:
                            text = element.get_text(strip=True)
                            if text and self.PRICE_PATTERN.search(text):
                                return re.sub(r'\s+', '', text)  # Remove whitespace
                    except Exception:
                        continue
        
        return None
    
    def _extract_with_scoring(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price using pattern matching and intelligent scoring"""
        candidates = []
        
        # Find all elements containing price patterns
        for index, element in enumerate(soup.find_all(string=False)):
            if not hasattr(element, 'get_text'):
                continue
                
            text = element.get_text(strip=True)
            if not text:
                continue
                
            # Remove whitespace for pattern matching
            text_no_ws = re.sub(r'\s+', '', text)
            matches = self.PRICE_PATTERN.findall(text_no_ws)
            
            if matches and len(matches) == 1:
                # Create candidate with the matched price
                price_match = ''.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
                candidate = PriceCandidate(element, price_match, index)
                candidates.append(candidate)
        
        if not candidates:
            return None
        
        # Score each candidate
        for i, candidate in enumerate(candidates):
            candidate.score = self._score_element(candidate, i)
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Return the highest-scored price
        if candidates:
            return candidates[0].price_match
        
        return None
    
    def _score_element(self, candidate: PriceCandidate, index: int) -> float:
        """
        Score price candidate based on multiple factors
        Higher score = more likely to be the actual price
        """
        score = 0.0
        element = candidate.element
        text = candidate.text
        text_no_ws = re.sub(r'\s+', '', text)
        price = candidate.price_match
        
        # Positive scoring factors
        
        # 1. Element mentions 'price' - strong indicator
        if re.search(r'price', text, re.IGNORECASE):
            score += 10
        
        # 2. Price format quality
        if '.' in price:  # Has decimal point
            score += 4
        if ',' in price:  # Has comma separator  
            score += 2
        if re.search(r'[1-9]', text_no_ws):  # Contains non-zero digit
            score += 2
        
        # 3. HTML tag bonuses
        if element.name and re.match(r'^(h1|h2|h3|h4|h5|b|strong|span)$', element.name, re.IGNORECASE):
            score += 1
        
        # 4. Class and ID attribute analysis
        attributes = element.get('class', []) + [element.get('id', '')]
        attribute_text = ' '.join(filter(None, attributes)).lower()
        
        # Positive class/id patterns
        positive_patterns = r'total|price|sale|now|prc|current|cost|amount'
        if re.search(positive_patterns, attribute_text):
            score += 10
        
        # 5. Parent element analysis (look up the tree)
        parent_count = 0
        current = element.parent
        while current and parent_count < 2:
            if hasattr(current, 'get'):
                parent_attrs = current.get('class', []) + [current.get('id', '')]
                parent_attr_text = ' '.join(filter(None, parent_attrs)).lower()
                if re.search(positive_patterns, parent_attr_text):
                    score += 5  # Less weight for parent matches
            current = current.parent
            parent_count += 1
        
        # Negative scoring factors
        
        # 1. Penalize if no attributes (likely plain text)
        if not element.attrs:
            score -= 10
        
        # 2. Negative class/id patterns
        negative_patterns = r'original|header|items|under|cart|more|nav|upsell|old|was|list|rrp|bundle|shipping|tax|vat'
        if re.search(negative_patterns, attribute_text):
            score -= 5
        
        # 3. Bad HTML tags
        if element.name and re.match(r'(script|style|link|meta|del|a)$', element.name, re.IGNORECASE):
            score -= 100
        
        # 4. Hidden elements
        style = element.get('style', '')
        if 'display:none' in re.sub(r'\s+', '', style.lower()):
            score -= 100
        
        # 5. Length penalty (very long text is less likely to be a price)
        score -= len(text) / 100
        
        # 6. Position penalty (later elements are less likely to be the main price)
        score -= index * 0.1
        
        return score
    
    def _clean_price(self, price_text: str) -> str:
        """Clean and normalize price text"""
        if not price_text:
            return price_text
        
        # Handle array case (shouldn't happen in Python, but defensive)
        if isinstance(price_text, list):
            price_text = price_text[0] if price_text else ""
        
        # Extract numeric value
        numeric_match = self.NUMERIC_PATTERN.search(price_text)
        if numeric_match:
            numeric_value = numeric_match.group(0)
            
            # Handle comma as thousand separator vs decimal
            if ',' in numeric_value and '.' in numeric_value:
                # Both comma and dot - comma is thousand separator
                numeric_value = numeric_value.replace(',', '')
            elif ',' in numeric_value and '.' not in numeric_value:
                # Only comma - could be decimal (European) or thousand separator
                # Heuristic: if more than 2 digits after comma, it's thousand separator
                parts = numeric_value.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Likely decimal comma, convert to dot
                    numeric_value = numeric_value.replace(',', '.')
                else:
                    # Likely thousand separator, remove
                    numeric_value = numeric_value.replace(',', '')
            
            try:
                # Parse and format to 2 decimal places
                parsed_price = float(numeric_value)
                return f"{parsed_price:.2f}"
            except ValueError:
                # If parsing fails, return original cleaned text
                return re.sub(r'[^\d.,]', '', price_text)
        
        return price_text


# Global instance for use in extractor service
intelligent_price_extractor = IntelligentPriceExtractor()