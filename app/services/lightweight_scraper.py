"""
Lightweight hybrid scraping service
Combines requests + Playwright for optimal performance and success rate
"""

import asyncio
import os
import time
import random
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from fake_useragent import UserAgent


class LightweightScraper:
    """Hybrid scraping service: requests first, Playwright fallback"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", 2))
        self.requests_timeout = 15  # Fast timeout for requests
        self.playwright_timeout = 30000  # Longer timeout for complex sites
        
        # Headers for requests (more comprehensive to avoid blocking)
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',  # UK preference first
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',  # More realistic for production
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"'
        }
    
    async def initialize_playwright(self):
        """Initialize Playwright browser (lazy loading)"""
        # Check if browser is still connected before trying to reuse
        if self.browser:
            try:
                # Test browser connection
                contexts = self.browser.contexts
                print("🎭 Reusing existing Playwright browser")
                return
            except Exception as e:
                print(f"⚠️ Existing browser disconnected: {e}")
                self.browser = None
                self.playwright = None
        
        if not self.browser:
            print("🎭 Initializing Playwright browser...")
            try:
                self.playwright = await async_playwright().start()
                
                # Use Chromium with cloud-optimized settings for Render.com
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',  # Required for cloud deployment
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',  # Block images for speed
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--single-process',  # Use single process for low memory
                        '--no-zygote',  # Better for containerized environments
                        '--memory-pressure-off',
                        '--max_old_space_size=512',  # Limit memory usage
                    ]
                )
                
                print("✅ Playwright browser initialized")
            except Exception as e:
                print(f"⚠️ Playwright initialization failed: {e}")
                print("🔄 Playwright will be unavailable, using requests-only mode")
                self.browser = None
                self.playwright = None
    
    def try_requests_scraping(self, url: str, retry_count: int = 0) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Try fast requests-based scraping first
        Returns: (success, html_content, metadata)
        """
        start_time = time.time()
        max_retries = 2 if os.getenv('RENDER_SERVICE_NAME') or os.getenv('RENDER') else 1
        
        try:
            print(f"🚀 Trying requests scraping for {urlparse(url).netloc}" + 
                  (f" (retry {retry_count + 1})" if retry_count > 0 else ""))
            
            session = requests.Session()
            
            # Create dynamic headers with fresh user agent
            headers = self.base_headers.copy()
            headers['User-Agent'] = self.ua.random
            
            # Add domain-specific headers for better success
            domain = urlparse(url).netloc.lower()
            if 'currys' in domain:
                headers['Referer'] = 'https://www.google.co.uk/'
                headers['Sec-Fetch-Site'] = 'cross-site'
            elif 'amazon' in domain:
                headers['Referer'] = 'https://www.amazon.co.uk/'
                headers['Sec-Fetch-Site'] = 'same-origin'
            elif 'smythstoys' in domain:
                headers['Referer'] = 'https://www.google.co.uk/'
                headers['Sec-Fetch-Site'] = 'cross-site'
            elif 'thetoyshop' in domain:
                headers['Referer'] = 'https://www.google.co.uk/'
                headers['Sec-Fetch-Site'] = 'cross-site'
            
            session.headers.update(headers)
            
            # Add random delay to mimic human behavior (longer in production)
            is_production = os.getenv('RENDER_SERVICE_NAME') or os.getenv('RENDER')
            if is_production:
                delay = random.uniform(1.0, 4.0)  # Longer delays for production
            else:
                delay = random.uniform(0.5, 2.5)  # Shorter delays for development
            time.sleep(delay)
            
            response = session.get(url, timeout=self.requests_timeout, allow_redirects=True)
            
            if response.status_code == 200:
                processing_time = int((time.time() - start_time) * 1000)
                
                # Quick check if content looks like it has product data
                content_lower = response.text.lower()
                product_indicators = ['price', 'add to cart', 'buy now', 'product', 'description']
                
                if any(indicator in content_lower for indicator in product_indicators):
                    metadata = {
                        'method': 'requests',
                        'status_code': response.status_code,
                        'processing_time': processing_time,
                        'content_length': len(response.text)
                    }
                    
                    print(f"✅ Requests scraping successful ({processing_time}ms)")
                    return True, response.text, metadata
                else:
                    print("⚠️ Requests got content but no product indicators found")
            else:
                print(f"❌ Requests failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            error_type = type(e).__name__
            print(f"❌ Requests failed ({error_type}): {str(e)[:150]}")
            
            # Retry logic for production
            if retry_count < max_retries - 1:
                retry_delay = random.uniform(2.0, 5.0)
                print(f"🔄 Retrying in {retry_delay:.1f}s...")
                time.sleep(retry_delay)
                return self.try_requests_scraping(url, retry_count + 1)
                
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ Requests error ({error_type}): {str(e)[:150]}")
        
        return False, None, None
    
    async def try_playwright_scraping(self, url: str, wait_for: str = "load", timeout: int = 30000) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Fallback to Playwright for complex sites
        Returns: (success, html_content, metadata)
        """
        start_time = time.time()
        page = None
        
        try:
            print(f"🎭 Trying Playwright scraping for {urlparse(url).netloc}")
            
            await self.initialize_playwright()
            
            # Check if browser is available after initialization
            if not self.browser:
                print("❌ Playwright browser not available")
                return False, None, None
            
            # Create fresh context with anti-detection measures
            context = None
            try:
                context = await self.browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent=self.ua.random,
                    # Anti-detection measures
                    java_script_enabled=True,
                    ignore_https_errors=True,
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    }
                )
                
                page = await context.new_page()
                
                # Anti-detection: Remove automation indicators
                await page.evaluate("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Mock plugins and languages
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Mock chrome property
                    window.chrome = {
                        runtime: {},
                    };
                    
                    // Mock permissions - safe version
                    if (navigator.permissions) {
                        const originalQuery = navigator.permissions.query;
                        navigator.permissions.query = (parameters) => {
                            if (parameters && parameters.name === 'notifications') {
                                return Promise.resolve({ state: 'default' });
                            }
                            if (originalQuery) {
                                return originalQuery(parameters);
                            }
                            return Promise.resolve({ state: 'granted' });
                        };
                    }
                """)
            
                # Set up request interception to block unnecessary resources
                await page.route("**/*", self._handle_playwright_route)
                
                # Navigate with timeout
                await page.goto(url, wait_until=wait_for, timeout=min(timeout, self.playwright_timeout))
                
                # Get page content
                content = await page.content()
                
                processing_time = int((time.time() - start_time) * 1000)
                
                metadata = {
                    'method': 'playwright',
                    'processing_time': processing_time,
                    'content_length': len(content),
                    'wait_for': wait_for
                }
                
                # Clean up context
                await context.close()
                
                print(f"✅ Playwright scraping successful ({processing_time}ms)")
                return True, content, metadata
                
            except Exception as inner_e:
                print(f"❌ Context creation failed: {inner_e}")
                return False, None, None
        
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"❌ Playwright failed: {error_msg}")
            
            # Try with different wait condition if timeout
            if wait_for != "domcontentloaded" and "timeout" in error_msg.lower():
                print("🔄 Retrying with domcontentloaded...")
                # Clean up current context first
                if 'context' in locals() and context:
                    try:
                        await context.close()
                    except:
                        pass
                return await self.try_playwright_scraping(url, "domcontentloaded", timeout)
        
        finally:
            # Always cleanup page and context
            if 'page' in locals() and page:
                try:
                    if not page.is_closed():
                        await page.close()
                except Exception as e:
                    print(f"⚠️ Warning closing page: {e}")
            
            # Close context if it exists
            if 'context' in locals() and context:
                try:
                    await context.close()
                except Exception as e:
                    print(f"⚠️ Warning closing context: {e}")
        
        return False, None, None
    
    async def _handle_playwright_route(self, route):
        """Block unnecessary resources in Playwright"""
        resource_type = route.request.resource_type
        
        # Block heavy resources but allow essential ones
        if resource_type in ["image", "stylesheet", "font", "media"]:
            await route.abort()
        else:
            await route.continue_()
    
    async def scrape_url(self, url: str, timeout: int = 30000, wait_for: str = "load") -> Dict[str, Any]:
        """
        Main scraping method with hybrid approach
        1. Try requests first (fast)
        2. Fallback to Playwright (reliable)
        """
        overall_start = time.time()
        
        try:
            # Step 1: Try requests scraping first
            success, content, metadata = self.try_requests_scraping(url)
            
            # Step 2: If requests failed, try Playwright (if available)
            if not success:
                print("🔄 Falling back to Playwright...")
                try:
                    success, content, metadata = await self.try_playwright_scraping(url, wait_for, timeout)
                except Exception as e:
                    print(f"⚠️ Playwright fallback failed: {e}")
                    success, content, metadata = False, None, None
            
            if success and content:
                return {
                    'success': True,
                    'content': content,
                    'metadata': metadata,
                    'total_time': int((time.time() - overall_start) * 1000)
                }
            else:
                return {
                    'success': False,
                    'error': 'Both requests and Playwright scraping failed',
                    'total_time': int((time.time() - overall_start) * 1000)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Scraping failed: {str(e)}',
                'total_time': int((time.time() - overall_start) * 1000)
            }
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"⚠️ Warning closing browser: {e}")
        
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"⚠️ Warning stopping playwright: {e}")
        
        print("🔒 Lightweight scraper closed")
    
    def is_healthy(self) -> bool:
        """Health check"""
        return True  # Requests is always available, Playwright loads on demand


# Global instance
lightweight_scraper = LightweightScraper()