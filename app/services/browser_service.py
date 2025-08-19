"""
Browser service for managing Camoufox instances
"""

import os
import asyncio
from typing import Optional
from camoufox import AsyncCamoufox


class BrowserService:
    """Service for managing Camoufox browser instances"""
    
    def __init__(self):
        self.browser: Optional[AsyncCamoufox] = None
        self.browser_context: Optional[AsyncCamoufox] = None
        self.active_pages = 0
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", 2))
        self.is_initializing = False
        self._page_semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def initialize(self):
        """Initialize the browser instance"""
        if self.browser or self.is_initializing:
            return
            
        self.is_initializing = True
        try:
            print("🦊 Initializing Camoufox browser...")
            
            # Create browser context manager
            self.browser_context = AsyncCamoufox(
                headless=True,
                # Optimize for performance and stability
                addons=[],  # Start with no addons for faster startup
            )
            
            # Start the browser
            self.browser = await self.browser_context.__aenter__()
            
            print("✅ Camoufox browser initialized successfully")
            
        except Exception as error:
            print(f"❌ Failed to initialize browser: {error}")
            self.browser = None
            self.browser_context = None
            raise Exception("Browser initialization failed")
        finally:
            self.is_initializing = False
    
    async def get_page(self):
        """Get a new page from the browser"""
        await self._page_semaphore.acquire()
        
        try:
            if not self.browser:
                await self.initialize()
            
            if not self.browser:
                raise Exception("Browser not available")
            
            # Create new page
            page = await self.browser.new_page()
            self.active_pages += 1
            
            # Configure page for scraping
            await self._configure_page(page)
            
            return page
            
        except Exception as e:
            self._page_semaphore.release()
            raise e
    
    async def _configure_page(self, page):
        """Configure page settings for optimal scraping"""
        # Set viewport
        await page.set_viewport_size({"width": 1366, "height": 768})
        
        # Set extra HTTP headers (including user agent)
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Block unnecessary resources for faster loading
        await page.route("**/*", self._handle_route)
    
    async def _handle_route(self, route):
        """Handle page routes to block unnecessary resources"""
        resource_type = route.request.resource_type
        
        # Block images, stylesheets, fonts for faster loading
        if resource_type in ["image", "stylesheet", "font"]:
            await route.abort()
        else:
            await route.continue_()
    
    async def close_page(self, page):
        """Close a page and release resources"""
        try:
            if page and not page.is_closed():
                await page.close()
                self.active_pages = max(0, self.active_pages - 1)
        except Exception as e:
            print(f"⚠️ Error closing page: {e}")
        finally:
            self._page_semaphore.release()
    
    async def close(self):
        """Close the browser instance"""
        if self.browser_context:
            try:
                await self.browser_context.__aexit__(None, None, None)
                print("🔒 Browser closed")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
            finally:
                self.browser = None
                self.browser_context = None
                self.active_pages = 0
    
    async def restart(self):
        """Restart the browser instance"""
        print("🔄 Restarting browser...")
        await self.close()
        await self.initialize()
    
    def is_healthy(self) -> bool:
        """Check if browser is healthy"""
        return self.browser is not None