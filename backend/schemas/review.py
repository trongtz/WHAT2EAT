from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReviewBase(BaseModel):
    """Base schema cho Review"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema để tạo review"""
    reservation_id: UUID


class ReviewResponse(ReviewBase):
    """Schema để trả về review"""
    review_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    reservation_id: UUID
    status: str  # PENDING, APPROVED, REJECTED
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)