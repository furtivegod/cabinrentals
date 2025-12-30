"""
Pydantic schemas for FAQ API
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class FAQBase(BaseModel):
    """Base FAQ schema"""
    question: str
    answer: str
    slug: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    display_order: int = 0
    status: str = "published"
    is_featured: bool = False


class FAQResponse(FAQBase):
    """FAQ response schema"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    class Config:
        from_attributes = True


class FAQListResponse(BaseModel):
    """FAQ list response with pagination"""
    faqs: List[FAQResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

