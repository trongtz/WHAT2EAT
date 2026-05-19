from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    availability_status: str = "AVAILABLE"
    is_available: Optional[bool] = None

    @model_validator(mode="after")
    def normalize_availability(self):
        if self.is_available is not None:
            self.availability_status = "AVAILABLE" if self.is_available else "UNAVAILABLE"
        return self


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    availability_status: Optional[str] = None
    is_available: Optional[bool] = None

    @model_validator(mode="after")
    def normalize_availability(self):
        if self.is_available is not None:
            self.availability_status = "AVAILABLE" if self.is_available else "UNAVAILABLE"
        return self


class MenuItemResponse(BaseModel):
    id: Optional[UUID] = None
    item_id: Optional[UUID] = None
    restaurant_id: UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    category: Optional[str] = None
    image_url: Optional[str] = None
    availability_status: str
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


DishBase = MenuItemBase
DishCreate = MenuItemCreate
DishUpdate = MenuItemUpdate
DishResponse = MenuItemResponse
