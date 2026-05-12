from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str
    phone: str = Field(..., max_length=20)
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    open_hours: Optional[str] = None
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    max_capacity: int = Field(..., gt=0)


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    open_hours: Optional[str] = None
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    max_capacity: Optional[int] = Field(default=None, gt=0)


class RestaurantResponse(RestaurantBase):
    restaurant_id: UUID
    owner_id: UUID
    average_rating: Decimal
    review_count: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    max_capacity: Optional[int] = None
    available_capacity: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RestaurantAdminResponse(RestaurantResponse):
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None


class RestaurantStatusUpdate(BaseModel):
    status: str
