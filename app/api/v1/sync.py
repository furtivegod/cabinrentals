"""
Sync API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.post("/sync/properties")
async def sync_properties(db: Session = Depends(get_db)):
    """
    Trigger property sync
    """
    # TODO: Implement property sync
    return {"status": "syncing"}

