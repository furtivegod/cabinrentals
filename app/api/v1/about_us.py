"""
About Us API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase
from app.schemas.about_us import AboutUsResponse
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/about-us", response_model=AboutUsResponse)
async def get_about_us(
    supabase: Client = Depends(get_supabase)
):
    """
    Get the About Us page
    
    Returns the about us page with title "About Us"
    """
    # Query for about us page with exact title "About Us"
    result = supabase.from_('about_us_pages').select('*').eq('title', 'About Us').eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError("About Us page not found")
    
    return result.data[0]


@router.get("/about-us/{about_id}", response_model=AboutUsResponse)
async def get_about_us_by_id(
    about_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an about us page by ID
    """
    result = supabase.from_('about_us_pages').select('*').eq('id', about_id).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"About Us page with ID {about_id} not found")
    
    return result.data[0]


@router.get("/about-us/slug/{slug}", response_model=AboutUsResponse)
async def get_about_us_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get an about us page by slug
    """
    result = supabase.from_('about_us_pages').select('*').eq('slug', slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"About Us page with slug '{slug}' not found")
    
    return result.data[0]

