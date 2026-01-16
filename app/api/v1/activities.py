"""
Activities API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import Optional, List
from math import ceil

from app.dependencies import get_supabase
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("/activities/getAllActivities")
async def getAllActivities(
    supabase: Client = Depends(get_supabase)
):
    """
    Get all activities
    """
    result = supabase.from_('activities').select('*').execute()
    return result.data

@router.get("/activities")
async def list_activities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (published, draft, archived)"),
    activity_type_tid: Optional[int] = Query(None, description="Filter by activity type term ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    List all activities with pagination and filtering
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by status (published, draft, archived)
    - **activity_type_tid**: Filter by activity type taxonomy term ID
    """
    # Build query
    query = supabase.from_('activities').select('*', count='exact')
    
    # Apply filters
    if status_filter:
        query = query.eq('status', status_filter)
    else:
        # Default to published only if no status filter
        query = query.eq('status', 'published')
    
    if activity_type_tid:
        query = query.eq('activity_type_tid', activity_type_tid)
    
    # Get total count first (without pagination)
    count_result = query.execute()
    total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
    
    # Apply ordering and pagination
    query = query.order('display_order', desc=False)
    query = query.order('is_featured', desc=True)
    query = query.order('published_at', desc=True)
    query = query.order('created_at', desc=True)
    query = query.range((page - 1) * page_size, page * page_size - 1)
    
    # Execute query
    result = query.execute()
    activities = result.data if result.data else []
    
    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return {
        'activities': activities,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@router.get("/activities/{activity_id}")
async def get_activity(
    activity_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an activity by ID
    
    Returns an activity by its UUID.
    """
    result = supabase.from_('activities').select('*').eq('id', activity_id).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Activity with ID '{activity_id}' not found")
    
    return result.data[0]


@router.get("/activities/slug/{slug}")
async def get_activity_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an activity by slug
    
    Only returns published activities.
    """
    result = supabase.from_('activities').select('*').eq('slug', slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Activity with slug '{slug}' not found")
    
    return result.data[0]


@router.get("/activities/activity-slug/{activity_slug:path}")
async def get_activity_by_activity_slug(
    activity_slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an activity by activity_slug (full URL path from Drupal)
    
    Only returns published activities.
    Handles multi-segment slugs like 'hiking/trail-name' or 'fishing/river-spot'
    """
    result = supabase.from_('activities').select('*').eq('activity_slug', activity_slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Activity with activity_slug '{activity_slug}' not found")
    
    return result.data[0]
