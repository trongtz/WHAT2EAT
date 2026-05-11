# File: models/notification.py
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    type = Column(String(100), nullable=False)  # RESERVATION_CONFIRMED, REVIEW_APPROVED, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # reservation_id, review_id, etc.
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
