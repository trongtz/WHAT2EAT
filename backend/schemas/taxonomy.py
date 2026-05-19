from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CuisineCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CuisineCategoryResponse(CuisineCategoryCreate):
    category_id: UUID

    model_config = ConfigDict(from_attributes=True)


class RestaurantImageCreate(BaseModel):
    image_url: str = Field(..., min_length=1)
    image_type: str = Field(default="general", max_length=50)


class RestaurantImageResponse(RestaurantImageCreate):
    image_id: UUID
    restaurant_id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantCuisineLink(BaseModel):
    category_id: UUID
