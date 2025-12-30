"""
Policy API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase
from app.schemas.policy import PolicyResponse
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/policies", response_model=PolicyResponse)
async def get_rental_policies(
    supabase: Client = Depends(get_supabase)
):
    """
    Get the Rental Policies page
    
    Returns the policy page with title "Rental Policies"
    """
    # Query for policy with exact title "Rental Policies"
    result = supabase.from_('policies').select('*').eq('title', 'Rental Policies').eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError("Rental Policies page not found")
    
    return result.data[0]


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy_by_id(
    policy_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a policy by ID
    """
    result = supabase.from_('policies').select('*').eq('id', policy_id).execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Policy with ID {policy_id} not found")
    
    return result.data[0]


@router.get("/policies/slug/{slug}", response_model=PolicyResponse)
async def get_policy_by_slug(
    slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a policy by slug
    """
    result = supabase.from_('policies').select('*').eq('slug', slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Policy with slug '{slug}' not found")
    
    return result.data[0]

