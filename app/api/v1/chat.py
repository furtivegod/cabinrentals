"""
Chat API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.post("/chat")
async def chat_message(db: Session = Depends(get_db)):
    """
    Handle chat messages
    """
    # TODO: Implement chat functionality
    return {"message": None}

