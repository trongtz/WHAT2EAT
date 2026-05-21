from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.user import User
from services.ai_assistant.conversation_context import get_conversation_context
from services.ai_assistant.intent_extractor import extract_intent, filters_from_intent, intent_to_dict
from services.ai_assistant.recommendation_engine import RecommendationEngine
from services.ai_assistant.response_composer import compose_recommendation_response
from services.ai_assistant.tools import passes_hard_constraints, search_restaurants_tool
from services.ai_assistant.user_preferences import get_user_preference_tool


class AIAssistantService:
    def __init__(self, recommendation_engine: RecommendationEngine | None = None) -> None:
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def generate_recommendation(
        self,
        query: str,
        db: Session,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        current_user: User | None = None,
        session_id=None,
        limit: int = 5,
    ) -> dict[str, Any]:
        base_intent = extract_intent(query)
        conversation_context = get_conversation_context(db, session_id, query, base_intent)
        intent = extract_intent(
            query,
            previous_query=conversation_context["previous_query"] if conversation_context["use_previous_context"] else None,
        )
        filters_applied = filters_from_intent(intent)
        user_profile = get_user_preference_tool(db, current_user)
        previous_result_ids = set(conversation_context["previous_result_ids"])
        candidates = [
            restaurant
            for restaurant in search_restaurants_tool(db)
            if passes_hard_constraints(restaurant, intent)
            and (
                not conversation_context["avoid_repeated_results"]
                or str(restaurant.restaurant_id) not in previous_result_ids
            )
        ]
        matches, total_found = self.recommendation_engine.rank_restaurants_tool(
            db,
            candidate_restaurants=candidates,
            intent=intent,
            query=query,
            latitude=latitude,
            longitude=longitude,
            user_profile=user_profile,
            limit=limit,
        )
        response = compose_recommendation_response(
            query=query,
            matches=matches,
            total_found=total_found,
            intent=intent,
            filters_applied=filters_applied,
        )
        response["intent"] = intent_to_dict(intent)
        response["context_used"] = {
            "previous_query": conversation_context["previous_query"],
            "previous_result_ids": conversation_context["previous_result_ids"],
            "use_previous_context": conversation_context["use_previous_context"],
            "avoid_repeated_results": conversation_context["avoid_repeated_results"],
        }
        return response
