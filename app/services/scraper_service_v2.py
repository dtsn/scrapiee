"""
Updated scraper service using lightweight hybrid approach
"""

import time
from typing import Dict, Any
from .lightweight_scraper import lightweight_scraper
from .extractor_service import ExtractorService


class ScraperServiceV2:
    """Lightweight scraping service with hybrid approach"""
    
    def __init__(self):
        self.extractor = ExtractorService()
        self.scraper = lightweight_scraper
    
    async def scrape_url(self, url: str, timeout: int = 30000, wait_for: str = "load") -> Dict[str, Any]:
        """
        Main scraping method with error handling and classification
        """
        start_time = time.time()
        
        # Ensure URL is string (convert from Pydantic HttpUrl if needed)
        url_str = str(url)
        
        try:
            print(f"🕷️ Starting scrape for: {url_str}")
            
            # Scrape with hybrid approach
            result = await self.scraper.scrape_url(url_str, timeout, wait_for)
            
            if result['success']:
                # Extract product data from HTML content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(result['content'], 'html.parser')
                
                # Create a mock page object for extractor compatibility
                class MockPage:
                    def __init__(self, content):
                        self.content_data = content
                    
                    async def content(self):
                        return self.content_data
                    
                    async def wait_for_load_state(self, state, timeout):
                        pass  # No-op for static content
                
                mock_page = MockPage(result['content'])
                
                # Extract product data
                product_data = await self.extractor.extract_product_data(mock_page, url_str)
                
                processing_time = int((time.time() - start_time) * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "title": product_data.get("title"),
                        "price": product_data.get("price"),
                        "currency": product_data.get("currency", "USD"),
                        "description": product_data.get("description"),
                        "image": product_data.get("image"),
                        "url": url_str
                    },
                    "error": None,
                    "metadata": {
                        "timestamp": int(time.time()),
                        "processing_time": processing_time,
                        "extraction_method": f"hybrid-{result['metadata']['method']}",
                        "scraper_time": result['total_time'],
                        "content_size": result['metadata']['content_length']
                    }
                }
            else:
                # Classify error type
                error_code, error_message = self._classify_error(result['error'], url_str)
                
                return {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": error_code,
                        "message": error_message,
                        "details": result['error']
                    },
                    "metadata": {
                        "timestamp": int(time.time()),
                        "processing_time": int((time.time() - start_time) * 1000),
                        "extraction_method": "hybrid-failed"
                    }
                }
                
        except Exception as e:
            error_code, error_message = self._classify_error(str(e), url_str)
            
            return {
                "success": False,
                "data": None,
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": str(e)
                },
                "metadata": {
                    "timestamp": int(time.time()),
                    "processing_time": int((time.time() - start_time) * 1000),
                    "extraction_method": "hybrid-error"
                }
            }
    
    def _classify_error(self, error_msg: str, url: str) -> tuple[str, str]:
        """Classify error types for better debugging"""
        error_lower = error_msg.lower()
        
        if "timeout" in error_lower:
            return "TIMEOUT", "Request timed out while loading the page"
        elif "connection" in error_lower and "refused" in error_lower:
            return "CONNECTION_REFUSED", "Server refused the connection"
        elif "name resolution" in error_lower or "dns" in error_lower:
            return "DNS_ERROR", "Unable to resolve domain name"
        elif "invalid" in error_lower and "url" in error_lower:
            return "INVALID_URL", "The provided URL is not valid"
        elif "403" in error_msg or "forbidden" in error_lower:
            return "FORBIDDEN", "Access to the website was forbidden"
        elif "404" in error_msg or "not found" in error_lower:
            return "NOT_FOUND", "The requested page was not found"
        elif "rate limit" in error_lower or "429" in error_msg:
            return "RATE_LIMITED", "Rate limited by the target website"
        else:
            return "SCRAPING_FAILED", "General scraping failure"
    
    async def close(self):
        """Clean up resources"""
        await self.scraper.close()
    
    def is_healthy(self) -> bool:
        """Health check"""
        return self.scraper.is_healthy()


# Global instance
scraper_service_v2 = ScraperServiceV2()