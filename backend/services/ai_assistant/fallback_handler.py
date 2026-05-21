from __future__ import annotations

from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse, AIRestaurantMatch


def fallback_keyword_search_tool(db: Session, request: AIRecommendationRequest, error: Exception) -> AIRecommendationResponse:
    restaurants = crud_restaurant.search_restaurants(db, query=request.query, limit=5)
    matches = [_restaurant_to_ai_match(restaurant) for restaurant in restaurants]
    return AIRecommendationResponse(
        message=f"Recommend system chưa phản hồi được ({type(error).__name__}). Hệ thống đã chuyển sang tìm kiếm cơ bản.",
        total_found=len(matches),
        recommended_restaurants=matches,
        session_id=request.session_id,
        source="FALLBACK",
    )


def fallback_trace_payload(response: AIRecommendationResponse, error: Exception, query: str) -> dict[str, object]:
    return {
        "extracted_intent": {"error": type(error).__name__},
        "filters_applied": {"fallback_query": query},
        "result_restaurant_ids": [str(match.id) for match in response.recommended_restaurants],
    }


def _restaurant_to_ai_match(restaurant) -> AIRestaurantMatch:
    return AIRestaurantMatch(
        id=str(restaurant.restaurant_id),
        name=restaurant.name,
        address=restaurant.address,
        distance_km=None,
        match_score=max(0.0, min(1.0, float(restaurant.average_rating or 0) / 5)),
        reason="Fallback keyword search result",
    )
