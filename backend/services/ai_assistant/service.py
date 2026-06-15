from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.user import User
from services.ai_assistant.agent import handle_agent_turn
from services.ai_assistant.conversation_context import apply_conversation_memory, get_conversation_context
from services.ai_assistant.intent_extractor import extract_intent, filters_from_intent, intent_to_dict, intent_value
from services.ai_assistant.openai_reranker import (
    AgenticRerankError,
    agentic_shortlist_size,
    rerank_shortlist,
    should_use_agentic_reranker,
)
from services.ai_assistant.recommend_imports import haversine_km, normalize_text
from services.ai_assistant.recommendation_engine import RecommendationEngine
from services.ai_assistant.response_composer import compose_recommendation_response
from services.ai_assistant.tools import (
    check_available_slots_tool,
    parse_radius_km_from_query,
    passes_hard_constraints,
    passes_location_constraint,
    search_restaurants_tool,
)
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
        latitude, longitude, location_anchor = _resolve_location_anchor(query, latitude, longitude)
        base_intent = extract_intent(query)
        conversation_context = get_conversation_context(db, session_id, query, base_intent)
        agent_response = handle_agent_turn(
            db=db,
            query=query,
            current_user=current_user,
            session_id=session_id,
            conversation_context=conversation_context,
            latitude=latitude,
            longitude=longitude,
        )
        if agent_response:
            agent_response["intent"] = intent_to_dict(base_intent)
            agent_response["context_used"] = {
                "previous_query": conversation_context["previous_query"],
                "previous_result_ids": conversation_context["previous_result_ids"],
                "use_previous_context": conversation_context["use_previous_context"],
                "avoid_repeated_results": conversation_context["avoid_repeated_results"],
            }
            return agent_response
        if conversation_context["use_previous_context"]:
            intent = extract_intent(query, previous_query=conversation_context["previous_query"])
        else:
            intent = base_intent
        intent = apply_conversation_memory(intent, conversation_context["recent_user_queries"])
        intent = _apply_negative_overrides(intent)
        filters_applied = filters_from_intent(intent)
        radius_km = parse_radius_km_from_query(query) if latitude is not None and longitude is not None else None
        if radius_km is not None and intent_value(intent, "walking_only", False):
            radius_km = min(radius_km, 1.5)
        filters_applied["radius_km"] = radius_km
        if location_anchor:
            filters_applied["location_anchor"] = location_anchor
        direct_response = _build_distance_lookup_response(db, query, latitude, longitude)
        if direct_response:
            direct_response["filters_applied"] = filters_applied
            direct_response["intent"] = intent_to_dict(intent)
            direct_response["context_used"] = {
                "previous_query": conversation_context["previous_query"],
                "previous_result_ids": conversation_context["previous_result_ids"],
                "use_previous_context": conversation_context["use_previous_context"],
                "avoid_repeated_results": conversation_context["avoid_repeated_results"],
            }
            return direct_response
        user_profile = get_user_preference_tool(db, current_user)
        previous_result_ids = set(conversation_context["previous_result_ids"])
        candidates = [
            restaurant
            for restaurant in search_restaurants_tool(
                db,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
            )
            if passes_hard_constraints(restaurant, intent, db=db)
            and passes_location_constraint(
                restaurant,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
            )
            and (
                not conversation_context["avoid_repeated_results"]
                or str(restaurant.restaurant_id) not in previous_result_ids
            )
        ]
        use_agentic_reranker = should_use_agentic_reranker()
        shortlist_limit = agentic_shortlist_size(limit) if use_agentic_reranker else limit
        matches, total_found = self.recommendation_engine.rank_restaurants_tool(
            db,
            candidate_restaurants=candidates,
            intent=intent,
            query=query,
            latitude=latitude,
            longitude=longitude,
            user_profile=user_profile,
            limit=shortlist_limit,
        )
        agentic_metadata = {
            "enabled": use_agentic_reranker,
            "used": False,
            "shortlist_size": len(matches),
        }
        message_override = None
        source = "HYBRID"
        if use_agentic_reranker and matches:
            try:
                agentic_result = rerank_shortlist(
                    query=query,
                    intent=intent,
                    recent_user_queries=conversation_context["recent_user_queries"],
                    matches=matches,
                    limit=limit,
                )
                matches = agentic_result.matches
                message_override = agentic_result.assistant_message
                source = "HYBRID_AGENTIC"
                agentic_metadata["used"] = True
            except AgenticRerankError:
                matches = matches[:limit]
                agentic_metadata["fallback"] = "offline_ranking"
        else:
            matches = matches[:limit]
        response = compose_recommendation_response(
            query=query,
            matches=matches,
            total_found=total_found,
            intent=intent,
            filters_applied=filters_applied,
            message_override=message_override,
            source=source,
        )
        response["agentic"] = agentic_metadata
        response["intent"] = intent_to_dict(intent)
        response["context_used"] = {
            "previous_query": conversation_context["previous_query"],
            "previous_result_ids": conversation_context["previous_result_ids"],
            "use_previous_context": conversation_context["use_previous_context"],
            "avoid_repeated_results": conversation_context["avoid_repeated_results"],
        }
        return response


def _resolve_location_anchor(
    query: str,
    latitude: float | None,
    longitude: float | None,
) -> tuple[float | None, float | None, dict[str, Any] | None]:
    normalized_query = normalize_text(query)
    demo_location_keywords = [
        "khoa hoc tu nhien",
        "dh khtn",
        "dai hoc khoa hoc tu nhien",
        "linh trung",
        "lang dai hoc",
        "dhqg",
        "dai hoc quoc gia",
        "ky tuc xa",
        "ktx",
        "khu a",
        "khu b",
    ]
    if not any(keyword in normalized_query for keyword in demo_location_keywords):
        return latitude, longitude, None

    demo_latitude = 10.875
    demo_longitude = 106.8
    return (
        demo_latitude,
        demo_longitude,
        {
            "label": "ĐH Khoa học Tự nhiên - Linh Trung",
            "latitude": demo_latitude,
            "longitude": demo_longitude,
            "source": "demo_keyword",
        },
    )


def _build_distance_lookup_response(
    db: Session,
    query: str,
    latitude: float | None,
    longitude: float | None,
) -> dict[str, Any] | None:
    normalized_query = normalize_text(query)
    if not any(phrase in normalized_query for phrase in ["bao xa", "cach may km", "khoang cach"]):
        return None

    matches = [
        restaurant
        for restaurant in search_restaurants_tool(db)
        if normalize_text(restaurant.name) and normalize_text(restaurant.name) in normalized_query
    ]
    if not matches:
        return {
            "message": "Mình chưa xác định được quán bạn muốn hỏi khoảng cách. Bạn ghi rõ tên quán giúp mình nhé.",
            "total_found": 0,
            "result_restaurant_ids": [],
            "recommended_restaurants": [],
            "source": "HYBRID",
        }

    restaurant = max(matches, key=lambda item: len(normalize_text(item.name)))
    distance_km = haversine_km(
        latitude,
        longitude,
        float(restaurant.latitude) if restaurant.latitude is not None else None,
        float(restaurant.longitude) if restaurant.longitude is not None else None,
    )
    if distance_km is None:
        message = f"Mình đã tìm thấy {restaurant.name}, nhưng cần vị trí hiện tại của bạn để tính khoảng cách."
        reason = "Chưa có vị trí người dùng để tính khoảng cách."
    else:
        message = f"Từ vị trí hiện tại tới {restaurant.name} khoảng {distance_km:.1f} km."
        reason = f"Cách bạn khoảng {distance_km:.1f} km."
    restaurant_id = str(restaurant.restaurant_id)
    return {
        "message": message,
        "total_found": 1,
        "result_restaurant_ids": [restaurant_id],
        "recommended_restaurants": [
            {
                "id": restaurant_id,
                "name": restaurant.name,
                "address": restaurant.address,
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "match_score": 1.0,
                "reason": reason,
                "available_capacity": check_available_slots_tool(db, restaurant),
                "quality_score": None,
                "availability_score": None,
                "quality_signals": None,
            }
        ],
        "source": "HYBRID",
    }


def _apply_negative_overrides(intent: Any) -> Any:
    excluded_cuisines = set(intent_value(intent, "excluded_cuisines", []) or [])
    cuisines = [
        cuisine
        for cuisine in (intent_value(intent, "cuisines", []) or [])
        if cuisine not in excluded_cuisines
    ]
    excluded_keywords = [normalize_text(keyword) for keyword in (intent_value(intent, "excluded_keywords", []) or [])]
    dish_terms = [
        dish
        for dish in (intent_value(intent, "dish_terms", []) or [])
        if not any(keyword in normalize_text(dish) for keyword in excluded_keywords)
    ]
    if isinstance(intent, dict):
        intent["cuisines"] = cuisines
        intent["dish_terms"] = dish_terms
    else:
        intent.cuisines = cuisines
        intent.dish_terms = dish_terms
    return intent
