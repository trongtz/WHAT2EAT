from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CheckInCreate(BaseModel):
    restaurant_id: UUID
    reservation_id: Optional[UUID] = None
    menu_item_id: Optional[UUID] = None
    crowd_status: Optional[str] = Field(default=None, max_length=50)
    note: Optional[str] = None


class CheckInResponse(BaseModel):
    checkin_id: UUID
    customer_id: UUID
    restaurant_id: UUID
    reservation_id: Optional[UUID] = None
    menu_item_id: Optional[UUID] = None
    checkin_at: datetime
    crowd_status: Optional[str] = None
    note: Optional[str] = None
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
