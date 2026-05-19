from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from services.opening_hours_service import get_primary_open_hours, normalize_opening_hours


class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    address: str
    phone: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    opening_hours: Optional[Any] = None
    open_hours: Optional[Any] = None
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    cuisine_category_ids: Optional[List[UUID]] = None
    price_range: Optional[str] = None

    @model_validator(mode="after")
    def normalize_legacy_fields(self):
        if self.opening_hours is None and self.open_hours is not None:
            self.opening_hours = self.open_hours
        return self


class RestaurantCreate(RestaurantBase):
    max_capacity: int = Field(..., gt=0)


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    opening_hours: Optional[Any] = None
    open_hours: Optional[Any] = None
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    cuisine_category_ids: Optional[List[UUID]] = None
    price_range: Optional[str] = None
    max_capacity: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def normalize_legacy_fields(self):
        if self.opening_hours is None and self.open_hours is not None:
            self.opening_hours = self.open_hours
        return self


class RestaurantResponse(BaseModel):
    restaurant_id: UUID
    owner_id: UUID
    name: str
    address: str
    phone: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    opening_hours: Optional[Any] = None
    open_hours: Optional[Any] = None
    price_range: Optional[str] = None
    rating_avg: Decimal
    average_rating: Decimal
    review_count: Optional[int] = None
    menu_count: Optional[int] = None
    approval_status: str
    status: str
    is_active: bool
    images: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    max_capacity: Optional[int] = None
    available_capacity: Optional[int] = None
    max_tables: Optional[int] = None
    available_tables: Optional[int] = None

    @model_validator(mode="after")
    def normalize_response_open_hours(self):
        self.open_hours = get_primary_open_hours(self.opening_hours or self.open_hours)
        self.opening_hours = normalize_opening_hours(self.opening_hours or self.open_hours)
        if self.max_tables is None:
            self.max_tables = self.max_capacity
        if self.available_tables is None:
            self.available_tables = self.available_capacity
        return self

    model_config = ConfigDict(from_attributes=True)


class RestaurantAdminResponse(RestaurantResponse):
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None


class RestaurantStatusUpdate(BaseModel):
    status: Optional[str] = None
    approval_status: Optional[str] = None
    reason: Optional[str] = None

    @property
    def normalized_status(self) -> str:
        return (self.approval_status or self.status or "").strip().upper()
