"""
Pydantic schemas for Blog API
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class BlogBase(BaseModel):
    """Base blog schema"""
    title: str
    slug: str
    body: Optional[str] = None
    body_summary: Optional[str] = None
    body_format: str = "filtered_html"
    author_name: Optional[str] = None
    status: str = "published"
    is_promoted: bool = False
    is_sticky: bool = False


class BlogResponse(BlogBase):
    """Blog response schema"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    class Config:
        from_attributes = True


class BlogListResponse(BaseModel):
    """Blog list response with pagination"""
    blogs: List[BlogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
