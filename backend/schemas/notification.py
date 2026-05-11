from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Schema để trả về notification"""
    notification_id: UUID
    user_id: UUID
    type: str
    title: str
    content: str
    reference_id: Optional[UUID] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MarkNotificationAsRead(BaseModel):
    """Schema để đánh dấu notification đã đọc"""
    is_read: bool = True
