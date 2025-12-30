"""
Booking API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.post("/bookings")
async def create_booking(db: Session = Depends(get_db)):
    """
    Create a new booking
    """
    # TODO: Implement booking creation
    return {"booking": None}

