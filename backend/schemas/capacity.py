from typing import Optional
from uuid import UUID
from datetime import time, date
from pydantic import BaseModel, ConfigDict


class CapacityBase(BaseModel):
    """Base schema cho Capacity"""
    day_of_week: int  # 0-6
    start_time: time
    end_time: time
    max_capacity: int


class CapacityCreate(CapacityBase):
    """Schema để tạo capacity"""
    restaurant_id: UUID


class CapacityUpdate(BaseModel):
    """Schema để update capacity"""
    max_capacity: Optional[int] = None


class CapacityResponse(CapacityBase):
    """Schema để trả về capacity"""
    capacity_id: UUID
    start_time: time
    end_time: time
    max_capacity: int  # Đây là "Tổng số bàn"
    current_booked: int = 0 # Số bàn đã được đặt (Tính từ bảng Reservations)
    
    @property
    def available_capacity(self) -> int:
        # Số bàn trống = Tổng - Đã đặt
        return max(0, self.max_capacity - self.current_booked)

    model_config = ConfigDict(from_attributes=True)


class CapacityOverrideBase(BaseModel):
    """Base schema cho CapacityOverride"""
    override_date: date
    start_time: time
    end_time: time
    max_capacity: int
    note: Optional[str] = None


class CapacityOverrideCreate(CapacityOverrideBase):
    """Schema để tạo capacity override"""
    restaurant_id: UUID


class CapacityOverrideResponse(CapacityOverrideBase):
    """Schema để trả về capacity override"""
    override_id: UUID
    restaurant_id: UUID

    model_config = ConfigDict(from_attributes=True)