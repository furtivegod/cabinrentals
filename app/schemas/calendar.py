"""
Calendar schema definitions
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime


class CalendarState(BaseModel):
    """Availability calendar state"""
    sid: int
    css_class: str
    label: Optional[str] = None
    weight: int = 0
    is_available: bool = False

    class Config:
        from_attributes = True


class CalendarAvailability(BaseModel):
    """Availability record for a specific date"""
    cid: int
    date: date
    sid: int
    state: Optional[CalendarState] = None  # Populated when joining with states

    class Config:
        from_attributes = True


class DailyRate(BaseModel):
    """Daily rate for a specific date"""
    id: str
    cabin_id: Optional[str] = None
    streamline_id: int
    date: date
    daily_rate: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalendarMonthResponse(BaseModel):
    """Calendar month data with availability and rates"""
    year: int
    month: int
    availability: Dict[str, CalendarAvailability]  # date string -> availability
    rates: Dict[str, DailyRate]  # date string -> rate
    states: List[CalendarState]  # All available states


class CabinCalendarResponse(BaseModel):
    """Cabin calendar information"""
    cabin_id: str
    calendar_id: int
    streamline_id: Optional[int] = None
    months: List[CalendarMonthResponse]  # Multiple months of data

    class Config:
        from_attributes = True

