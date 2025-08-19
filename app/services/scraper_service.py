"""
Main scraper service that orchestrates browser and extraction services
"""

import time
from typing import Optional
from urllib.parse import urlparse

from app.models import ScrapeResponse, ProductData, ResponseMetadata
from app.services.browser_service import BrowserService
from app.services.extractor_service import ExtractorService


class ScraperService:
    """Main service for coordinating web scraping operations"""
    
    def __init__(self, browser_service: BrowserService):
        self.browser_service = browser_service
        self.extractor_service = ExtractorService()
    
    async def scrape_product(
        self, 
        url: str, 
        timeout: int = 30000, 
        wait_for: str = "networkidle"
    ) -> ScrapeResponse:
        """
        Scrape product data from a URL
        
        Args:
            url: The URL to scrape
            timeout: Timeout in milliseconds
            wait_for: Wait condition ('networkidle', 'load', 'domcontentloaded')
            
        Returns:
            ScrapeResponse with extracted data or error information
        """
        start_time = time.time()
        page = None
        
        try:
            # Convert Pydantic URL to string if needed
            url_str = str(url)
            
            # Validate URL
            parsed_url = urlparse(url_str)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            print(f"🔍 Starting scrape for: {url_str}")
            
            # Check browser health
            if not self.browser_service.is_healthy():
                print("🔄 Browser unhealthy, restarting...")
                await self.browser_service.restart()
            
            # Get page from browser service
            page = await self.browser_service.get_page()
            
            # Navigate to the URL
            print(f"🌐 Navigating to {url_str}...")
            
            wait_until_options = {
                "networkidle": "networkidle",
                "load": "load", 
                "domcontentloaded": "domcontentloaded"
            }
            
            wait_until = wait_until_options.get(wait_for, "networkidle")
            
            try:
                await page.goto(url_str, wait_until=wait_until, timeout=timeout)
            except Exception as nav_error:
                # Try with a more lenient wait condition
                if wait_for == "networkidle":
                    print("⚠️ NetworkIdle failed, trying with load event...")
                    await page.goto(url_str, wait_until="load", timeout=timeout // 2)
                else:
                    raise nav_error
            
            print("📊 Page loaded, extracting data...")
            
            # Extract product data
            product_data = await self.extractor_service.extract_product_data(page, url_str)
            
            # Create response
            processing_time = int((time.time() - start_time) * 1000)
            
            response = ScrapeResponse(
                success=True,
                data=ProductData(**product_data),
                metadata=ResponseMetadata(
                    timestamp=int(time.time()),
                    processing_time=processing_time,
                    extraction_method="smart-selectors"
                )
            )
            
            print(f"✅ Scraping successful for {url_str}")
            return response
            
        except Exception as error:
            print(f"❌ Scraping failed for {url_str}: {str(error)}")
            
            processing_time = int((time.time() - start_time) * 1000)
            error_code = self._classify_error(error)
            
            response = ScrapeResponse(
                success=False,
                error={
                    "code": error_code,
                    "message": self._get_error_message(error_code),
                    "details": str(error)
                },
                metadata=ResponseMetadata(
                    timestamp=int(time.time()),
                    processing_time=processing_time
                )
            )
            
            return response
            
        finally:
            # Always close the page
            if page:
                await self.browser_service.close_page(page)
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate error code"""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return "TIMEOUT"
        elif "net::err_name_not_resolved" in error_str:
            return "DNS_ERROR"
        elif "net::err_connection_refused" in error_str:
            return "CONNECTION_REFUSED"
        elif "invalid url" in error_str:
            return "INVALID_URL"
        elif "browser" in error_str and "initialization" in error_str:
            return "BROWSER_ERROR"
        else:
            return "SCRAPING_FAILED"
    
    def _get_error_message(self, error_code: str) -> str:
        """Get user-friendly error message"""
        messages = {
            "TIMEOUT": "Request timed out while loading the page",
            "DNS_ERROR": "Could not resolve the domain name", 
            "CONNECTION_REFUSED": "Connection to the server was refused",
            "INVALID_URL": "The provided URL is not valid",
            "BROWSER_ERROR": "Browser service error",
            "SCRAPING_FAILED": "Failed to scrape the provided URL"
        }
        return messages.get(error_code, "An unexpected error occurred")