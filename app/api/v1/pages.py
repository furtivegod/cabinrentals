"""
Pages API endpoints - for fetching content from field_data_body
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Optional
from pydantic import BaseModel

from app.dependencies import get_supabase
from app.core.exceptions import NotFoundError

router = APIRouter()


class PageContentResponse(BaseModel):
    entity_type: str
    bundle: str
    entity_id: int
    revision_id: Optional[int] = None
    language: str
    delta: int
    title: Optional[str] = None
    slug: Optional[str] = None
    body_value: Optional[str] = None
    body_summary: Optional[str] = None
    body_format: Optional[str] = None


@router.get("/pages/slug/{slug}", response_model=PageContentResponse)
async def get_page_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get page content by slug from field_data_body table
    
    - **slug**: URL slug (e.g., 'about-blue-ridge-ga')
    """
    # Query field_data_body by slug
    result = supabase.from_('field_data_body').select('*').eq('slug', slug).eq('deleted', 0).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Page with slug '{slug}' not found")
    
    return PageContentResponse(**result.data[0])


@router.get("/pages/title/{title}", response_model=PageContentResponse)
async def get_page_by_title(
    title: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get page content by title from field_data_body table
    
    - **title**: Page title
    """
    # Query field_data_body by title (case-insensitive)
    result = supabase.from_('field_data_body').select('*').ilike('title', title).eq('deleted', 0).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Page with title '{title}' not found")
    
    return PageContentResponse(**result.data[0])

