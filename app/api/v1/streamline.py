"""
Streamline PMS API endpoints

These endpoints interact with the Streamline vacation rental software
to fetch property data, availability, rates, etc.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date

from app.services.pms import StreamlineService, StreamlineAPIError, get_streamline_service


router = APIRouter(tags=["Streamline PMS"])


# ------------------------------------------------------------------
# Response Models
# ------------------------------------------------------------------

class StreamlinePropertyResponse(BaseModel):
    """Response model for a single property"""
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None


class StreamlinePropertyListResponse(BaseModel):
    """Response model for property list"""
    success: bool
    count: int
    properties: List[Dict[str, Any]]
    message: Optional[str] = None


class StreamlineAvailabilityResponse(BaseModel):
    """Response model for availability data"""
    success: bool
    property_id: int
    start_date: str
    end_date: str
    data: Dict[str, Any]
    message: Optional[str] = None


class StreamlineRatesResponse(BaseModel):
    """Response model for rates data"""
    success: bool
    property_id: int
    start_date: str
    end_date: str
    data: Dict[str, Any]
    message: Optional[str] = None


# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------

@router.get("/streamline/properties", response_model=StreamlinePropertyListResponse)
async def get_streamline_properties(
    include_inactive: bool = Query(False, description="Include inactive properties"),
    property_id: Optional[int] = Query(None, description="Specific property ID to fetch")
):
    """
    Get list of properties from Streamline PMS
    
    Returns all active properties by default. Use include_inactive=true to 
    include inactive properties as well. Optionally filter by specific property_id.
    """
    try:
        service = get_streamline_service()
        properties = await service.get_property_list(
            include_inactive=include_inactive,
            property_id=property_id
        )
        
        return StreamlinePropertyListResponse(
            success=True,
            count=len(properties),
            properties=properties
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )


@router.get("/streamline/properties/{property_id}", response_model=StreamlinePropertyResponse)
async def get_streamline_property_info(property_id: int):
    """
    Get detailed information for a specific property from Streamline
    
    Args:
        property_id: The Streamline property/unit ID
    """
    try:
        service = get_streamline_service()
        property_data = await service.get_property_info(property_id)
        
        return StreamlinePropertyResponse(
            success=True,
            data=property_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )


@router.get("/streamline/properties/{property_id}/images")
async def get_streamline_property_images(property_id: int):
    """
    Get images for a specific property from Streamline
    
    Args:
        property_id: The Streamline property/unit ID
    """
    try:
        service = get_streamline_service()
        images = await service.get_property_images(property_id)
        
        return {
            "success": True,
            "property_id": property_id,
            "count": len(images),
            "images": images
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )


@router.get("/streamline/properties/{property_id}/amenities")
async def get_streamline_property_amenities(property_id: int):
    """
    Get amenities for a specific property from Streamline
    
    Args:
        property_id: The Streamline property/unit ID
    """
    try:
        service = get_streamline_service()
        amenities = await service.get_property_amenities(property_id)
        
        return {
            "success": True,
            "property_id": property_id,
            "count": len(amenities),
            "amenities": amenities
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )


@router.get("/streamline/properties/{property_id}/availability", response_model=StreamlineAvailabilityResponse)
async def get_streamline_availability(
    property_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get availability for a property within a date range
    
    Args:
        property_id: The Streamline property/unit ID
        start_date: Start date for availability check
        end_date: End date for availability check
    """
    try:
        service = get_streamline_service()
        availability = await service.get_availability(
            property_id=property_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return StreamlineAvailabilityResponse(
            success=True,
            property_id=property_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            data=availability
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )


@router.get("/streamline/properties/{property_id}/rates", response_model=StreamlineRatesResponse)
async def get_streamline_rates(
    property_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get pricing/rates for a property within a date range
    
    Args:
        property_id: The Streamline property/unit ID
        start_date: Start date for rate lookup
        end_date: End date for rate lookup
    """
    try:
        service = get_streamline_service()
        rates = await service.get_rates(
            property_id=property_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return StreamlineRatesResponse(
            success=True,
            property_id=property_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            data=rates
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streamline configuration error: {str(e)}"
        )
    except StreamlineAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Streamline API error: {e.message}"
        )



