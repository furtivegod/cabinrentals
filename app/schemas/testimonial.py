"""
Pydantic schemas for Testimonial API
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TestimonialBase(BaseModel):
    """Base testimonial schema"""
    title: str
    slug: str
    body: Optional[str] = None
    body_summary: Optional[str] = None
    body_format: str = "filtered_html"
    cabin_name: Optional[str] = None
    cabin_drupal_nid: Optional[int] = None
    customer_image_url: Optional[str] = None
    customer_image_alt: Optional[str] = None
    customer_image_title: Optional[str] = None
    customer_image_width: Optional[int] = None
    customer_image_height: Optional[int] = None
    author_name: Optional[str] = None
    status: str = "published"
    is_featured: bool = False
    is_sticky: bool = False


class TestimonialResponse(TestimonialBase):
    """Testimonial response schema"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TestimonialListResponse(BaseModel):
    """Testimonial list response with pagination"""
    testimonials: List[TestimonialResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


