from __future__ import annotations

from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse, AIRestaurantMatch
from services.ai_assistant.intent_extractor import filters_from_intent
from services.ai_assistant.recommend_imports import parse_query_heuristically
from services.ai_assistant.recommendation_engine import RecommendationEngine
from services.ai_assistant.response_composer import compose_recommendation_response
from services.ai_assistant.tools import (
    parse_radius_km_from_query,
    passes_hard_constraints,
    passes_location_constraint,
    search_restaurants_tool,
)


def fallback_keyword_search_tool(db: Session, request: AIRecommendationRequest, error: Exception) -> AIRecommendationResponse:
    try:
        return _offline_recommendation_fallback(db, request, error)
    except Exception:
        return _basic_keyword_fallback(db, request, error)


def _offline_recommendation_fallback(
    db: Session,
    request: AIRecommendationRequest,
    error: Exception,
) -> AIRecommendationResponse:
    intent = parse_query_heuristically(request.query)
    radius_km = (
        parse_radius_km_from_query(request.query)
        if request.latitude is not None and request.longitude is not None
        else None
    )
    candidates = [
        restaurant
        for restaurant in search_restaurants_tool(db)
        if passes_hard_constraints(restaurant, intent, db=db)
        and passes_location_constraint(
            restaurant,
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=radius_km,
        )
    ]
    matches, total_found = RecommendationEngine().rank_restaurants_tool(
        db,
        candidate_restaurants=candidates,
        intent=intent,
        query=request.query,
        latitude=request.latitude,
        longitude=request.longitude,
        user_profile={"enabled": False},
        limit=5,
    )
    filters_applied = filters_from_intent(intent)
    filters_applied["radius_km"] = radius_km
    response = compose_recommendation_response(
        query=request.query,
        matches=matches,
        total_found=total_found,
        intent=intent,
        filters_applied=filters_applied,
        source="FALLBACK",
    )
    response["message"] = (
        f"Recommend system chưa phản hồi được ({type(error).__name__}). "
        "Hệ thống đã chuyển sang gợi ý dự phòng offline. "
        + response["message"]
    )
    response["session_id"] = request.session_id
    return AIRecommendationResponse(**response)


def _basic_keyword_fallback(db: Session, request: AIRecommendationRequest, error: Exception) -> AIRecommendationResponse:
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
    images = [image.image_url for image in getattr(restaurant, "restaurant_images", []) if getattr(image, "image_url", None)]
    return AIRestaurantMatch(
        id=str(restaurant.restaurant_id),
        name=restaurant.name,
        address=restaurant.address,
        images=images or None,
        image=images[0] if images else None,
        average_rating=float(restaurant.average_rating or 0),
        distance_km=None,
        match_score=max(0.0, min(1.0, float(restaurant.average_rating or 0) / 5)),
        reason="Fallback keyword search result",
    )
