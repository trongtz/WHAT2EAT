from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

import models.registry  # noqa: F401
from models.user import User
from services.ai_assistant.service import AIAssistantService


_assistant_service = AIAssistantService()


def generate_recommendation(
    query: str,
    db: Session,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    current_user: User | None = None,
    session_id=None,
    limit: int = 5,
) -> dict[str, Any]:
    return _assistant_service.generate_recommendation(
        query,
        db,
        latitude=latitude,
        longitude=longitude,
        current_user=current_user,
        session_id=session_id,
        limit=limit,
    )
