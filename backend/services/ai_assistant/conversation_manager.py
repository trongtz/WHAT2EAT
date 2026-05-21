from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

import crud.ai_chat as crud_ai_chat
import crud.search_history as crud_search_history
from models.user import User
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse
from schemas.ai_chat import AIChatMessageCreate, AIChatSessionUpdate, RecommendationLogCreate
from schemas.search_history import SearchHistoryCreate
from services.ai_assistant.conversation_context import summarize_context


def save_ai_trace(
    db: Session,
    request: AIRecommendationRequest,
    response: AIRecommendationResponse,
    current_user: User | None,
    *,
    extracted_intent: dict | None = None,
    filters_applied: dict | None = None,
    result_restaurant_ids: list[str] | None = None,
) -> None:
    session = None
    if request.session_id:
        session = crud_ai_chat.get_or_create_session(
            db,
            request.session_id,
            current_user.user_id if current_user else None,
            title=request.query[:150],
        )

    if session:
        crud_ai_chat.create_message(
            db,
            session.session_id,
            AIChatMessageCreate(
                role="user",
                content=request.query,
                extracted_intent=extracted_intent,
                processing_status="SUCCESS",
            ),
        )
        crud_ai_chat.create_message(
            db,
            session.session_id,
            AIChatMessageCreate(role="assistant", content=response.message, processing_status="SUCCESS"),
        )

    crud_search_history.create_search_history(
        db,
        SearchHistoryCreate(
            query_text=request.query,
            search_type=response.source if response.source in {"AI", "FALLBACK"} else "AI",
            filters_applied=filters_applied,
            extracted_entities=extracted_intent,
            result_restaurant_ids=result_restaurant_ids,
        ),
        current_user.user_id if current_user else None,
    )

    for index, restaurant in enumerate(response.recommended_restaurants, start=1):
        try:
            restaurant_id = UUID(str(restaurant.id))
        except ValueError:
            continue

        crud_ai_chat.create_recommendation_log(
            db,
            RecommendationLogCreate(
                session_id=session.session_id if session else None,
                customer_id=current_user.user_id if current_user else None,
                restaurant_id=restaurant_id,
                score=restaurant.match_score,
                reason=restaurant.reason,
                source=response.source,
                rank_position=index,
                prompt_summary=request.query,
            ),
        )

    if session:
        crud_ai_chat.update_session(
            db,
            session,
            AIChatSessionUpdate(
                context_summary=summarize_context(
                    request.query,
                    filters_applied,
                    result_restaurant_ids,
                )
            ),
        )
