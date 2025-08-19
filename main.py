#!/usr/bin/env python3
"""
Scrapiee - FastAPI Web Scraping Service
API-driven web scraping service using Camoufox for product data extraction
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from app.models import ScrapeRequest, ScrapeResponse, HealthResponse
from app.services.browser_service import BrowserService
from app.services.scraper_service import ScraperService

# Load environment variables
load_dotenv()

# Initialize services
browser_service = None
scraper_service = None

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global browser_service, scraper_service
    
    # Startup
    print("🚀 Starting Scrapiee API...")
    browser_service = BrowserService()
    scraper_service = ScraperService(browser_service)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Scrapiee API...")
    if browser_service:
        await browser_service.close()

# Create FastAPI app
app = FastAPI(
    title="Scrapiee API",
    description="API-driven web scraping service using Camoufox",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key authentication"""
    expected_key = os.getenv("SCRAPER_API_KEY")
    
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SERVER_MISCONFIGURATION",
                "message": "Server configuration error"
            }
        )
    
    if not credentials or credentials.credentials != expected_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "INVALID_API_KEY", 
                "message": "Invalid API key provided"
            }
        )
    return credentials.credentials


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Scrapiee API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=int(time.time()),
        uptime=int(time.time() - app.state.start_time) if hasattr(app.state, 'start_time') else 0
    )


@app.post("/api/scrape", response_model=ScrapeResponse)
@limiter.limit(f"{os.getenv('RATE_LIMIT_REQUESTS', 10)}/{os.getenv('RATE_LIMIT_WINDOW', 60)}minute")
async def scrape_url(
    request: Request,
    scrape_request: ScrapeRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Scrape product data from a URL
    
    Extracts title, price, currency, description, and image from the provided URL
    using intelligent element detection and Camoufox browser automation.
    """
    start_time = time.time()
    
    try:
        result = await scraper_service.scrape_product(
            url=scrape_request.url,
            timeout=scrape_request.timeout,
            wait_for=scrape_request.wait_for
        )
        
        # Add processing time
        result.metadata.processing_time = int((time.time() - start_time) * 1000)
        
        return result
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "SCRAPING_FAILED",
                    "message": "Failed to scrape the provided URL",
                    "details": str(e) if os.getenv("ENVIRONMENT") == "development" else None
                },
                "metadata": {
                    "timestamp": int(time.time()),
                    "processing_time": processing_time
                }
            }
        )


@app.get("/api/browser/status")
async def browser_status(api_key: str = Depends(verify_api_key)):
    """Get browser service status"""
    if not browser_service:
        raise HTTPException(status_code=503, detail="Browser service not available")
        
    return {
        "healthy": browser_service.is_healthy(),
        "active_pages": browser_service.active_pages,
        "max_concurrent_pages": browser_service.max_concurrent,
        "timestamp": int(time.time())
    }


@app.post("/api/browser/restart")
async def restart_browser(api_key: str = Depends(verify_api_key)):
    """Restart browser service"""
    if not browser_service:
        raise HTTPException(status_code=503, detail="Browser service not available")
        
    try:
        await browser_service.restart()
        return {
            "success": True,
            "message": "Browser restarted successfully",
            "timestamp": int(time.time())
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "timestamp": int(time.time())
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    # Store start time
    app.state.start_time = time.time()
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )