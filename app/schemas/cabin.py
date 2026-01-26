"""
Cabin schema definitions
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class CabinResponse(BaseModel):
    """Cabin response model"""
    id: str
    title: str
    slug: str
    cabin_slug: Optional[str] = None
    body: Optional[str] = None
    body_summary: Optional[str] = None
    body_format: str = "filtered_html"
    bedrooms: Optional[str] = None  # Bedroom count (from taxonomy term)
    bedrooms_tid: Optional[int] = None  # Taxonomy term ID
    bathrooms: Optional[str] = None  # Bathroom count (from taxonomy term)
    bathrooms_tid: Optional[int] = None  # Taxonomy term ID
    sleeps: Optional[int] = None
    minimum_rate: Optional[float] = None  # Minimum daily/nightly rate (DECIMAL in database)
    property_type: Optional[List[Any]] = None  # JSONB array: [{"tid": 20, "name": "Blue Ridge Luxury"}, ...]
    amenities: Optional[List[Any]] = None  # JSONB array: [{"tid": 131, "name": "Pet Friendly"}, ...]
    features: Optional[List[str]] = None
    featured_image_fid: Optional[int] = None
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_title: Optional[str] = None
    featured_image_width: Optional[int] = None
    featured_image_height: Optional[int] = None
    gallery_images: Optional[List[Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    streamline_id: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    author_name: Optional[str] = None
    status: str = "published"
    is_featured: bool = False
    is_sticky: bool = False
    display_order: int = 0
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    drupal_nid: Optional[int] = None
    drupal_vid: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Property list response model"""
    properties: List[CabinResponse]

