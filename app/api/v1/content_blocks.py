"""
Content blocks API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.get("/content-blocks")
async def list_content_blocks(db: Session = Depends(get_db)):
    """
    List content blocks
    """
    # TODO: Implement content block listing
    return {"content_blocks": []}

