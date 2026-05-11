from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class FavoriteCreate(BaseModel):
    """Schema để thêm nhà hàng vào yêu thích"""
    restaurant_id: UUID


class FavoriteResponse(BaseModel):
    """Schema để trả về favorite"""
    favorite_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
