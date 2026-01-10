"""
Taxonomy API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Optional
from pydantic import BaseModel

from app.dependencies import get_supabase
from app.core.exceptions import NotFoundError

router = APIRouter()


class TaxonomyTermResponse(BaseModel):
    tid: int
    vid: int
    name: str
    description: Optional[str] = None
    format: Optional[str] = None
    weight: int
    page_title: Optional[str] = None

@router.get("/taxonomy/term/by-category-slug", response_model=TaxonomyTermResponse)
async def get_term_by_category_slug(
    category: str,
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get taxonomy term by category and slug (mimics Drupal routing logic)
    
    - **category**: Route category ('all', 'amenities', or bedroom number)
    - **slug**: URL slug
    
    Logic:
    - If category is 'amenities', vid = 4
    - If category is not 'all' and not 'amenities', vid = 2 (bedrooms)
    - If category is 'all' and slug is not 'all', vid = 3 (property_type)
    """
    vid = None
    
    if category == 'amenities':
        vid = 4
    elif category != 'all':
        # Assume it's a bedroom category (vid = 2)
        vid = 2
    elif slug != 'all':
        # Property type (vid = 3)
        vid = 3
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category/slug combination"
        )
    
    # Convert slug to name - try both hyphenated and space-separated versions
    slug_name = slug.replace('-', ' ')
    
    # First try exact match (case-insensitive)
    result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', slug_name).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        # Try with hyphenated version
        result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', slug).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        # Try partial match
        result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', f'%{slug_name}%').limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Taxonomy term with category '{category}', slug '{slug}' not found")
    
    term = result.data[0]
    tid = term['tid']
    
    # Get page title from field_data_field_term_page_title
    page_title_result = supabase.from_('field_data_field_term_page_title').select('field_term_page_title_value').eq('entity_id', tid).eq('entity_type', 'taxonomy_term').eq('deleted', 0).limit(1).execute()
    
    page_title = None
    if page_title_result.data and len(page_title_result.data) > 0:
        page_title = page_title_result.data[0].get('field_term_page_title_value')
    
    return TaxonomyTermResponse(
        tid=tid,
        vid=term['vid'],
        name=term['name'],
        description=term.get('description'),
        format=term.get('format'),
        weight=term.get('weight', 0),
        page_title=page_title
    )




@router.get("/taxonomy/term/by-slug", response_model=TaxonomyTermResponse)
async def get_term_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get taxonomy term by slug
    """
    vid = None
    
    if slug == 'blue-ridge-cabins' or slug == 'blue-ridge-memories':
        vid = 11
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slug combination"
        )
    
    # Convert slug to name - try both hyphenated and space-separated versions
    slug_name = slug.replace('-', ' ')
    
    # First try exact match (case-insensitive)
    result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', slug_name).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        # Try with hyphenated version
        result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', slug).limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        # Try partial match
        result = supabase.from_('taxonomy_term_data').select('*').eq('vid', vid).ilike('name', f'%{slug_name}%').limit(1).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Taxonomy term with slug '{slug}' not found")
    
    term = result.data[0]
    tid = term['tid']
    
    # Get page title from field_data_field_term_page_title
    page_title_result = supabase.from_('field_data_field_term_page_title').select('field_term_page_title_value').eq('entity_id', tid).eq('entity_type', 'taxonomy_term').eq('deleted', 0).limit(1).execute()
    
    page_title = None
    if page_title_result.data and len(page_title_result.data) > 0:
        page_title = page_title_result.data[0].get('field_term_page_title_value')
    
    return TaxonomyTermResponse(
        tid=tid,
        vid=term['vid'],
        name=term['name'],
        description=term.get('description'),
        format=term.get('format'),
        weight=term.get('weight', 0),
        page_title=page_title
    )