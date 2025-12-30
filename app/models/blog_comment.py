"""
Blog comment model
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid


class BlogComment(Base):
    """Blog comment model"""
    __tablename__ = "blog_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blog_id = Column(UUID(as_uuid=True), ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Comment content
    author_name = Column(String(255))
    author_email = Column(String(255))
    author_url = Column(String(500))
    subject = Column(String(500))
    comment_body = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), default='approved', nullable=False, index=True)  # approved, pending, spam, deleted
    
    __table_args__ = (
        CheckConstraint("status IN ('approved', 'pending', 'spam', 'deleted')", name='blog_comments_status_check'),
    )
    
    # Drupal migration
    drupal_cid = Column(Integer, unique=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    blog = relationship("Blog", back_populates="comments")

