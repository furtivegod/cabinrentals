"""
Testimonial API endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from supabase import Client
from typing import Optional, List
from uuid import UUID
from math import ceil

from app.dependencies import get_supabase
from app.schemas.testimonial import TestimonialResponse, TestimonialListResponse
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/testimonials", response_model=TestimonialListResponse)
async def list_testimonials(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (published, draft, archived)"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    cabin_name: Optional[str] = Query(None, description="Filter by cabin name"),
    search: Optional[str] = Query(None, description="Search in title and body"),
    supabase: Client = Depends(get_supabase)
):
    """
    List all testimonials with pagination and filtering
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by status (published, draft, archived)
    - **featured**: Filter by featured status
    - **cabin_name**: Filter by cabin name
    - **search**: Search query to filter by title or body content
    """
    # Build query using Supabase client
    query = supabase.from_('testimonials').select('*', count='exact')
    
    # Apply filters
    if status_filter:
        query = query.eq('status', status_filter)
    else:
        # Default to published only if no status filter
        query = query.eq('status', 'published')
    
    if featured is not None:
        query = query.eq('is_featured', featured)
    
    if cabin_name:
        query = query.ilike('cabin_name', f'%{cabin_name}%')
    
    if search:
        # Supabase text search - search in title field
        # Note: For multi-column search, you can chain multiple filters or use full-text search
        query = query.ilike('title', f'%{search}%')
    
    # Get total count first (without pagination)
    count_query = query
    count_result = count_query.execute()
    total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
    
    # Apply ordering and pagination
    query = query.order('is_sticky', desc=True)
    query = query.order('is_featured', desc=True)
    query = query.order('published_at', desc=True)
    query = query.order('created_at', desc=True)
    query = query.range((page - 1) * page_size, page * page_size - 1)
    
    # Execute query
    result = query.execute()
    testimonials = result.data if result.data else []
    
    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return TestimonialListResponse(
        testimonials=testimonials,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/testimonials/{testimonial_id}", response_model=TestimonialResponse)
async def get_testimonial(
    testimonial_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a single testimonial by ID
    """
    result = supabase.from_('testimonials').select('*').eq('id', str(testimonial_id)).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Testimonial with ID {testimonial_id} not found")
    
    return result.data[0]


@router.get("/testimonials/slug/{slug}", response_model=TestimonialResponse)
async def get_testimonial_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a testimonial by slug
    
    Only returns published testimonials. This endpoint is used for public-facing testimonial pages.
    """
    result = supabase.from_('testimonials').select('*').eq('slug', slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Testimonial with slug '{slug}' not found")
    
    return result.data[0]


@router.get("/testimonials/featured", response_model=List[TestimonialResponse])
async def get_featured_testimonials(
    limit: int = Query(5, ge=1, le=20, description="Number of featured testimonials to return"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get featured testimonials
    """
    result = supabase.from_('testimonials').select('*').eq('status', 'published').eq('is_featured', True).order('published_at', desc=True).order('created_at', desc=True).limit(limit).execute()
    
    return result.data if result.data else []


@router.get("/testimonials/recent", response_model=List[TestimonialResponse])
async def get_recent_testimonials(
    limit: int = Query(5, ge=1, le=20, description="Number of recent testimonials to return"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get most recent testimonials
    """
    result = supabase.from_('testimonials').select('*').eq('status', 'published').order('published_at', desc=True).order('created_at', desc=True).limit(limit).execute()
    
    return result.data if result.data else []

