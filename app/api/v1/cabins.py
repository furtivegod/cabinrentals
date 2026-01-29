"""
Cabin API endpoints
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import Optional

from app.dependencies import get_supabase
from app.schemas.cabin import CabinResponse, PropertyListResponse
from app.core.exceptions import NotFoundError

router = APIRouter()


    
@router.get("/cabins/getAllCabins", response_model=PropertyListResponse)
async def getAllCabins(
    supabase: Client = Depends(get_supabase)
):
    """
    Get all cabins
    
    Only returns published cabins.
    """
    print("getAllCabins")
    result = supabase.from_('cabins').select('*').eq('status', 'published').execute()
    return PropertyListResponse(properties=result.data)

@router.get("/cabins/get-cabins-by-term-id", response_model=PropertyListResponse)
async def get_cabins_by_term_id(
    tid: Optional[int] = Query(None, description="The term ID to filter cabins by"),
    field: Optional[str] = Query(None, description="Field to search in: property_type, bedrooms, bathrooms, amenities (default: all)"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get cabins by term ID
    
    Searches for cabins where the specified term ID (tid) exists in:
    - property_type: JSONB array of objects like [{"tid": 20, "name": "Blue Ridge Luxury"}, ...]
    - amenities: JSONB array of objects like [{"tid": 131, "name": "Pet Friendly"}, ...]
    
    Note: bedrooms and bathrooms are now stored as string values only (no tid fields).
    
    If 'field' is specified, only searches in that field. Otherwise searches in all fields.
    
    Returns all matching cabins (no pagination).
    """
    # Build base query
    query = supabase.from_('cabins').select('*').eq('status', 'published')
    
    # Execute query to get all published cabins
    result = query.execute()
    
    if not result.data:
        return PropertyListResponse(properties=[])
    
    # Filter cabins by tid if provided
    filtered_cabins = []
    if tid is not None:
        # Determine which fields to search
        fields_to_search = []
        if field:
            # Search in specific field
            if field in ['property_type', 'amenities']:
                fields_to_search = [field]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid field '{field}'. Must be one of: property_type, amenities"
                )
        else:
            # Search in all fields
            fields_to_search = ['property_type', 'amenities']
        
        # Filter cabins where any of the specified fields contains the matching tid
        for cabin in result.data:
            found = False
            for field_name in fields_to_search:
                # For property_type and amenities, check JSONB arrays
                field_data = cabin.get(field_name)
                if field_data:
                    # Handle both list and JSON string formats
                    if isinstance(field_data, str):
                        try:
                            field_data = json.loads(field_data)
                        except (json.JSONDecodeError, TypeError):
                            continue
                    
                    # Check if field_data is a list and contains an object with matching tid
                    if isinstance(field_data, list):
                        for item in field_data:
                            if isinstance(item, dict) and item.get('tid') == tid:
                                found = True
                                break
                
                if found:
                    break
            
            if found:
                filtered_cabins.append(cabin)
    else:
        # No tid filter, return all published cabins
        filtered_cabins = result.data
    
    return PropertyListResponse(properties=filtered_cabins)


# @router.get("/cabins/slug/{slug}", response_model=CabinResponse)
# async def get_cabin_by_slug(
#     slug: str,
#     supabase: Client = Depends(get_supabase)
# ):
#     """
#     Get a cabin by slug
    
#     Only returns published cabins. This endpoint is used for public-facing cabin pages.
#     """
#     result = supabase.from_('cabins').select('*').eq('slug', slug).eq('status', 'published').execute()
    
#     if not result.data or len(result.data) == 0:
#         raise NotFoundError(f"Cabin with slug '{slug}' not found")
    
#     return result.data[0]


@router.get("/cabins/cabin-slug/{cabin_slug:path}", response_model=CabinResponse)
async def get_cabin_by_cabin_slug(
    cabin_slug: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a cabin by cabin_slug (original Drupal URL alias)
    
    This endpoint handles URLs like 'morganton/sanctuary' or 'blue-ridge/the-great-getaway'
    by matching against the cabin_slug field which stores the original Drupal URL alias.
    
    Only returns published cabins.
    """
    result = supabase.from_('cabins').select('*').eq('cabin_slug', cabin_slug).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Cabin with cabin_slug '{cabin_slug}' not found")
    
    return result.data[0]


@router.get("/cabins/{cabin_id}", response_model=CabinResponse)
async def get_cabin(
    cabin_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a cabin by ID
    
    Returns a cabin by its UUID.
    """
    result = supabase.from_('cabins').select('*').eq('id', cabin_id).eq('status', 'published').execute()
    
    if not result.data or len(result.data) == 0:
        raise NotFoundError(f"Cabin with ID '{cabin_id}' not found")
    
    return result.data[0]



