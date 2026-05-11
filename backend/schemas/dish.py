# File: schemas/dish.py
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    is_available: bool = True
    image_url: Optional[str] = None

class MenuItemCreate(MenuItemBase):
    """Schema để tạo món ăn - restaurant_id sẽ lấy từ URL params"""
    pass

class MenuItemUpdate(BaseModel):
    """Schema để update món ăn"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class MenuItemResponse(MenuItemBase):
    """Schema trả về danh sách món ăn"""
    id: Optional[UUID] = None
    item_id: Optional[UUID] = None
    restaurant_id: UUID

    model_config = ConfigDict(from_attributes=True)

# ---------------------------------------------------------
# BACKWARD COMPATIBILITY
# Giữ lại các tên cũ để không làm gãy các file router khác (như dishes.py)
# ---------------------------------------------------------
DishBase = MenuItemBase
DishCreate = MenuItemCreate
DishUpdate = MenuItemUpdate
DishResponse = MenuItemResponse