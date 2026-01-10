"""
About Us page model
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class AboutUsPage(Base):
    """About Us page model"""
    __tablename__ = "about_us"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core content
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    body = Column(Text)
    body_summary = Column(Text)
    body_format = Column(String(50), default='filtered_html')
    
    # Page section
    section = Column(String(100))  # main, history, team, mission, contact
    
    # Metadata
    author_id = Column(Integer)  # Reference to users table if you have one
    author_name = Column(String(255))
    
    # Publishing
    status = Column(String(20), default='published', nullable=False, index=True)  # published, draft, archived
    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    __table_args__ = (
        CheckConstraint("status IN ('published', 'draft', 'archived')", name='about_us_status_check'),
    )
    
    # SEO
    meta_title = Column(String(500))
    meta_description = Column(Text)
    
    # Drupal migration
    drupal_nid = Column(Integer, unique=True, index=True)
    drupal_vid = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

