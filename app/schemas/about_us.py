"""
Pydantic schemas for About Us API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AboutUsBase(BaseModel):
    """Base about us schema"""
    title: str
    slug: str
    body: Optional[str] = None
    body_summary: Optional[str] = None
    body_format: str = "filtered_html"
    section: Optional[str] = None
    author_name: Optional[str] = None
    status: str = "published"
    is_featured: bool = False
    display_order: int = 0


class AboutUsResponse(AboutUsBase):
    """About Us response schema"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    class Config:
        from_attributes = True

