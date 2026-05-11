from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class RestaurantBase(BaseModel):
    """Base schema cho Restaurant"""
    name: str = Field(..., min_length=1, max_length=255)
    address: str
    phone: str = Field(..., max_length=20)
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    open_hours: Optional[dict] = None  # {"mon": {"open": "08:00", "close": "22:00"}}
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None  # "cheap", "mid", "expensive"


class RestaurantCreate(RestaurantBase):
    """Schema để tạo restaurant"""
    pass


class RestaurantUpdate(BaseModel):
    """Schema để update restaurant"""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    open_hours: Optional[dict] = None
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None


class RestaurantResponse(RestaurantBase):
    """Schema trả về frontend"""
    restaurant_id: UUID
    owner_id: UUID
    average_rating: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)