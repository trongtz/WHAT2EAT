from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict # <-- Thêm ConfigDict

class FavoriteCreate(BaseModel):
    """Schema để thêm nhà hàng vào yêu thích"""
    restaurant_id: UUID

class FavoriteResponse(BaseModel):
    """Schema để trả về favorite"""
    favorite_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    created_at: datetime

    # <-- Thay thế class Config bằng model_config của Pydantic V2
    model_config = ConfigDict(from_attributes=True)