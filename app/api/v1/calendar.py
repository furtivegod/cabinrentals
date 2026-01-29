"""
Calendar API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import Optional, List
from datetime import date, datetime
from calendar import monthrange

from app.dependencies import get_supabase
from app.schemas.calendar import (
    CalendarState,
    CalendarAvailability,
    DailyRate,
    CalendarMonthResponse,
    CabinCalendarResponse
)

router = APIRouter()


@router.get("/calendar/states", response_model=List[CalendarState])
async def get_calendar_states(
    supabase: Client = Depends(get_supabase)
):
    """
    Get all availability calendar states
    """
    try:
        result = supabase.from_('availability_calendar_state').select('*').order('weight').execute()
        return [CalendarState(**state) for state in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendar states: {str(e)}")


@router.get("/calendar/cabin/{cabin_id}", response_model=CabinCalendarResponse)
async def get_cabin_calendar(
    cabin_id: str,
    months: int = Query(3, ge=1, le=12, description="Number of months to return"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to today"),
    include_rates: bool = Query(True, description="Include daily rates in response"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get calendar data for a cabin
    
    Returns availability and rates for the specified number of months.
    """
    try:
        # Get cabin calendar mapping
        mapping_result = supabase.from_('cabin_calendar_mapping').select('*').eq('cabin_id', cabin_id).execute()
        
        if not mapping_result.data:
            # Try to find by streamline_id if cabin_id mapping doesn't exist
            # First get the cabin to find streamline_id
            cabin_result = supabase.from_('cabins').select('streamline_id').eq('id', cabin_id).execute()
            if cabin_result.data and cabin_result.data[0].get('streamline_id'):
                streamline_id = cabin_result.data[0]['streamline_id']
                mapping_result = supabase.from_('cabin_calendar_mapping').select('*').eq('streamline_id', streamline_id).execute()
            
            if not mapping_result.data:
                raise HTTPException(status_code=404, detail="Calendar not found for this cabin. Please ensure the calendar data has been migrated.")
        
        mapping = mapping_result.data[0]
        calendar_id = mapping['calendar_id']
        streamline_id = mapping.get('streamline_id')
        
        # Parse start date
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start = date.today()
        
        # Get all calendar states
        states_result = supabase.from_('availability_calendar_state').select('*').order('weight').execute()
        states = {s['sid']: CalendarState(**s) for s in states_result.data}
        
        # Build months data
        months_data = []
        current_date = start
        
        for month_offset in range(months):
            year = current_date.year
            month = current_date.month
            
            # Calculate date range for this month
            first_day = date(year, month, 1)
            last_day_num = monthrange(year, month)[1]
            last_day = date(year, month, last_day_num)
            
            # Get availability for this month
            availability_result = supabase.from_('availability_calendar_availability').select('*').eq('cid', calendar_id).gte('date', str(first_day)).lte('date', str(last_day)).execute()
            
            availability_dict = {}
            for avail in availability_result.data:
                date_str = avail['date']
                sid = avail['sid']
                availability_dict[date_str] = CalendarAvailability(
                    cid=avail['cid'],
                    date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                    sid=sid,
                    state=states.get(sid)
                )
            
            # Get rates for this month if requested and streamline_id exists
            rates_dict = {}
            if include_rates and streamline_id:
                rates_result = supabase.from_('daily_rates').select('*').eq('streamline_id', streamline_id).gte('date', str(first_day)).lte('date', str(last_day)).execute()
                
                for rate in rates_result.data:
                    date_str = rate['date']
                    rates_dict[date_str] = DailyRate(
                        id=rate['id'],
                        cabin_id=rate.get('cabin_id'),
                        streamline_id=rate['streamline_id'],
                        date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                        daily_rate=float(rate['daily_rate']),
                        created_at=datetime.fromisoformat(rate['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(rate['updated_at'].replace('Z', '+00:00')) if rate.get('updated_at') else None
                    )
            
            months_data.append(CalendarMonthResponse(
                year=year,
                month=month,
                availability=availability_dict,
                rates=rates_dict,
                states=list(states.values())
            ))
            
            # Move to next month
            if month == 12:
                current_date = date(year + 1, 1, 1)
            else:
                current_date = date(year, month + 1, 1)
        
        return CabinCalendarResponse(
            cabin_id=cabin_id,
            calendar_id=calendar_id,
            streamline_id=streamline_id,
            months=months_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cabin calendar: {str(e)}")


@router.get("/calendar/cabin-slug/{slug:path}", response_model=CabinCalendarResponse)
async def get_cabin_calendar_by_slug(
    slug: str,
    months: int = Query(3, ge=1, le=12, description="Number of months to return"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to today"),
    include_rates: bool = Query(True, description="Include daily rates in response"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get calendar data for a cabin by slug
    
    Returns availability and rates for the specified number of months.
    """
    try:
        # First get the cabin by slug
        cabin_result = supabase.from_('cabins').select('id').eq('cabin_slug', slug).eq('status', 'published').execute()
        
        if not cabin_result.data:
            raise HTTPException(status_code=404, detail="Cabin not found")
        
        cabin_id = cabin_result.data[0]['id']
        
        # Use the cabin_id endpoint
        return await get_cabin_calendar(cabin_id, months, start_date, include_rates, supabase)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cabin calendar: {str(e)}")

