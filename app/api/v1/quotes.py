"""
Quote API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.post("/quotes")
async def generate_quote(db: Session = Depends(get_db)):
    """
    Generate a quote for a booking
    """
    # TODO: Implement quote generation
    return {"quote": None}

