from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    is_available: bool = True
    image_url: Optional[str] = None


class DishCreate(DishBase):
    """Schema để tạo dish - restaurant_id sẽ lấy từ URL params"""
    pass


class DishUpdate(BaseModel):
    """Schema để update dish"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None


class DishResponse(DishBase):
    id: Optional[UUID] = None
    item_id: Optional[UUID] = None  # UUID name
    restaurant_id: UUID

    class Config:
        from_attributes = True
