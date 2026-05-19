from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FavoriteCreate(BaseModel):
    restaurant_id: UUID


class FavoriteResponse(BaseModel):
    favorite_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteToggleResponse(BaseModel):
    restaurant_id: UUID
    is_favorite: bool
