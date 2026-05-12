from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReservationBase(BaseModel):
    """Base schema cho Reservation"""
    restaurant_id: UUID
    reservation_time: datetime
    guest_count: int = Field(..., gt=0, le=100)
    notes: Optional[str] = None


class ReservationCreate(ReservationBase):
    """Schema để tạo reservation"""
    pass  # customer_id sẽ lấy từ Token


class ReservationUpdate(BaseModel):
    """Schema để update reservation"""
    reservation_time: Optional[datetime] = None
    guest_count: Optional[int] = None
    notes: Optional[str] = None


class ReservationResponse(ReservationBase):
    """Schema để trả về reservation"""
    reservation_id: UUID
    customer_id: UUID
    status: str  # PENDING, CONFIRMED, REJECTED, CANCELLED
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Backward compatibility
BookingBase = ReservationBase
BookingCreate = ReservationCreate
BookingResponse = ReservationResponse