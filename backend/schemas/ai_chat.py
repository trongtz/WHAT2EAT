from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIChatSessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=150)


class AIChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=150)
    context_summary: Optional[str] = None
    status: Optional[str] = None


class AIChatSessionResponse(BaseModel):
    session_id: UUID
    customer_id: Optional[UUID] = None
    title: Optional[str] = None
    context_summary: Optional[str] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIChatMessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    extracted_intent: Optional[dict[str, Any]] = None
    processing_status: str = "SUCCESS"


class AIChatMessageResponse(BaseModel):
    message_id: UUID
    session_id: UUID
    role: str
    content: str
    extracted_intent: Optional[dict[str, Any]] = None
    processing_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationLogCreate(BaseModel):
    session_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    restaurant_id: UUID
    score: Optional[Decimal] = Field(default=None, ge=0, le=1)
    reason: Optional[str] = None
    source: Optional[str] = None
    rank_position: Optional[int] = None
    prompt_summary: Optional[str] = None
    model_version: Optional[str] = None


class RecommendationLogResponse(RecommendationLogCreate):
    log_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
