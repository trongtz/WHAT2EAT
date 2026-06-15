from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    reservation_id: Optional[UUID] = None


class ReviewResponse(ReviewBase):
    review_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    restaurant_name: Optional[str] = None
    reservation_id: Optional[UUID] = None
    status: str
    rejection_reason: Optional[str] = None
    userName: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
