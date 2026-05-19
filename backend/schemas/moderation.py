from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModerationLogCreate(BaseModel):
    target_type: str = Field(..., max_length=50)
    target_id: UUID
    action: str = Field(..., max_length=50)
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_reason_for_sensitive_actions(self):
        if self.action.upper() in {"REJECT", "BAN"} and not self.reason:
            raise ValueError("reason is required for REJECT or BAN actions")
        return self


class ModerationLogResponse(ModerationLogCreate):
    log_id: UUID
    admin_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
