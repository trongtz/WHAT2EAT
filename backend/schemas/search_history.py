from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchHistoryCreate(BaseModel):
    query_text: str = Field(..., min_length=1)
    search_type: str = "NORMAL"
    filters_applied: Optional[dict[str, Any]] = None
    extracted_entities: Optional[dict[str, Any]] = None
    result_restaurant_ids: Optional[list[str]] = None


class SearchHistoryResponse(SearchHistoryCreate):
    search_id: UUID
    customer_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
