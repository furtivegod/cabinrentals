"""
FAQ API endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from supabase import Client
from typing import Optional, List
from uuid import UUID
from math import ceil

from app.dependencies import get_supabase
from app.schemas.faq import FAQResponse, FAQListResponse
from app.core.exceptions import NotFoundError
from app.config import settings

router = APIRouter()


@router.get("/faqs/test", response_model=List[str])
async def get_faq_test():
    return settings.cors_origins_list

@router.get("/faqs", response_model=FAQListResponse)
async def list_faqs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (published, draft, archived)"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in question and answer"),
    supabase: Client = Depends(get_supabase)
):
    """
    List all FAQs with pagination and filtering
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by status (published, draft, archived)
    - **featured**: Filter by featured status
    - **category**: Filter by category
    - **search**: Search query to filter by question or answer content
    """
    # Build query using Supabase client
    query = supabase.from_('faqs').select('*', count='exact')
    
    # Apply filters
    if status_filter:
        query = query.eq('status', status_filter)
    else:
        # Default to published only if no status filter
        query = query.eq('status', 'published')
    
    if featured is not None:
        query = query.eq('is_featured', featured)
    
    if category:
        query = query.eq('category', category)
    
    if search:
        # Supabase text search - search in question field
        # Note: For multi-column search, you can chain multiple filters or use full-text search
        query = query.ilike('question', f'%{search}%')
    
    # Get total count first (without pagination)
    count_query = query
    count_result = count_query.execute()
    total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
    
    # Apply ordering and pagination
    query = query.order('display_order', desc=False)
    query = query.order('is_featured', desc=True)
    query = query.order('published_at', desc=True)
    query = query.order('created_at', desc=True)
    query = query.range((page - 1) * page_size, page * page_size - 1)
    
    # Execute query
    result = query.execute()
    faqs = result.data if result.data else []
    
    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return FAQListResponse(
        faqs=faqs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/faqs/{faq_id}", response_model=FAQResponse)
async def get_faq(
    faq_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a single FAQ by ID
    """
    result = supabase.from_('faqs').select('*').eq('id', str(faq_id)).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"FAQ with ID {faq_id} not found")
    
    return result.data[0]


@router.get("/faqs/slug/{slug}", response_model=FAQResponse)
async def get_faq_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an FAQ by slug
    """
    result = supabase.from_('faqs').select('*').eq('slug', slug).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"FAQ with slug '{slug}' not found")
    
    return result.data[0]


@router.get("/faqs/featured", response_model=List[FAQResponse])
async def get_featured_faqs(
    limit: int = Query(10, ge=1, le=50, description="Number of featured FAQs to return"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get featured FAQs
    """
    result = supabase.from_('faqs').select('*').eq('status', 'published').eq('is_featured', True).order('display_order', desc=False).order('published_at', desc=True).limit(limit).execute()
    
    return result.data if result.data else []


@router.get("/faqs/categories", response_model=List[str])
async def get_faq_categories(
    supabase: Client = Depends(get_supabase)
):
    """
    Get list of all FAQ categories
    """
    result = supabase.from_('faqs').select('category').eq('status', 'published').not_.is_('category', 'null').neq('category', '').execute()
    
    if not result.data:
        return []
    
    # Extract unique categories
    categories = set()
    for item in result.data:
        if item.get('category'):
            categories.add(item['category'])
    
    return sorted(list(categories))

@router.get("/faqs/category/{category}", response_model=List[FAQResponse])
async def get_faqs_by_category(
    category: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get all FAQs in a specific category
    """
    result = supabase.from_('faqs').select('*').eq('status', 'published').eq('category', category).order('display_order', desc=False).order('is_featured', desc=True).order('published_at', desc=True).execute()
    
    return result.data if result.data else []

