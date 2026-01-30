"""
Cabin schema definitions
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class CabinResponse(BaseModel):
    """Cabin response model"""
    id: str
    title: str
    cabin_slug: Optional[str] = None
    body: Optional[str] = None
    bedrooms: Optional[str] = None  # Bedroom count (from taxonomy term)
    bathrooms: Optional[str] = None  # Bathroom count (from taxonomy term)
    sleeps: Optional[int] = None
    property_type: Optional[List[Any]] = None  # JSONB array: [{"tid": 20, "name": "Blue Ridge Luxury"}, ...]
    amenities: Optional[List[Any]] = None  # JSONB array: [{"tid": 131, "name": "Pet Friendly"}, ...]
    features: Optional[List[str]] = None
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_title: Optional[str] = None
    gallery_images: Optional[List[Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    streamline_id: Optional[int] = None
    phone: Optional[str] = None
    keys_for_rent_id: Optional[int] = None
    flipkey_id: Optional[int] = None
    matterport_url: Optional[str] = None
    tagline: Optional[str] = None
    location: Optional[int] = None  # Location taxonomy term ID
    rates_description: Optional[str] = None
    analytics_code: Optional[str] = None
    video: Optional[List[Dict[str, Any]]] = None  # Array of video objects
    address: Optional[Dict[str, Any]] = None  # JSONB object: {country, address1, address2, city, state, zip_code}
    author_name: Optional[str] = None
    status: str = "published"
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    today_rate: Optional[float] = None  # Today's daily rate

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Property list response model"""
    properties: List[CabinResponse]
