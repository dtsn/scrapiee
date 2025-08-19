"""
Pydantic models for API requests and responses
"""

from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, Field


class ScrapeRequest(BaseModel):
    """Request model for scraping endpoint"""
    url: HttpUrl = Field(..., description="URL to scrape")
    timeout: Optional[int] = Field(30000, ge=1000, le=60000, description="Timeout in milliseconds")
    wait_for: Optional[Literal["networkidle", "load", "domcontentloaded"]] = Field(
        "networkidle", 
        description="Wait condition for page loading"
    )


class ProductData(BaseModel):
    """Product data model"""
    title: Optional[str] = Field(None, description="Product title")
    price: Optional[str] = Field(None, description="Product price")
    currency: Optional[str] = Field(None, description="Product currency")
    description: Optional[str] = Field(None, description="Product description")
    image: Optional[HttpUrl] = Field(None, description="Product image URL")
    url: str = Field(..., description="Source URL")


class ResponseMetadata(BaseModel):
    """Response metadata model"""
    timestamp: int = Field(..., description="Unix timestamp")
    processing_time: int = Field(..., description="Processing time in milliseconds")
    extraction_method: Optional[str] = Field("smart-selectors", description="Extraction method used")


class ScrapeResponse(BaseModel):
    """Response model for scraping endpoint"""
    success: bool = Field(..., description="Whether scraping was successful")
    data: Optional[ProductData] = Field(None, description="Extracted product data")
    error: Optional[dict] = Field(None, description="Error information if unsuccessful")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: int = Field(..., description="Unix timestamp")
    uptime: int = Field(..., description="Service uptime in seconds")