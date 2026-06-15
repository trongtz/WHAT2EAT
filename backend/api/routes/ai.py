from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_optional_current_user
from core.database import get_db
from models.user import User
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse, AIRestaurantMatch
from services.ai_assistant.conversation_manager import save_ai_trace
from services.ai_assistant.fallback_handler import fallback_keyword_search_tool, fallback_trace_payload
from services.ai_service import generate_recommendation

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendation(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    try:
        ai_data = generate_recommendation(
            request.query,
            db,
            latitude=request.latitude,
            longitude=request.longitude,
            current_user=current_user,
            session_id=request.session_id,
            limit=5,
        )

        ai_restaurants = ai_data.get("recommended_restaurants", [])
        response = AIRecommendationResponse(
            message=ai_data.get("message") or f"Tìm thấy {len(ai_restaurants)} nhà hàng phù hợp.",
            total_found=ai_data.get("total_found", len(ai_restaurants)),
            recommended_restaurants=[
                AIRestaurantMatch(
                    id=str(restaurant["id"]),
                    name=restaurant["name"],
                    address=restaurant["address"],
                    distance_km=restaurant.get("distance_km"),
                    match_score=restaurant.get("match_score"),
                    reason=restaurant.get("reason"),
                    available_capacity=restaurant.get("available_capacity"),
                    quality_score=restaurant.get("quality_score"),
                    availability_score=restaurant.get("availability_score"),
                    quality_signals=restaurant.get("quality_signals"),
                )
                for restaurant in ai_restaurants
            ],
            session_id=request.session_id,
            source=ai_data.get("source", "HYBRID"),
            agent=ai_data.get("agent"),
            booking=ai_data.get("booking"),
        )
        try:
            save_ai_trace(
                db,
                request,
                response,
                current_user,
                extracted_intent=ai_data.get("intent"),
                filters_applied=ai_data.get("filters_applied"),
                result_restaurant_ids=ai_data.get("result_restaurant_ids"),
                agent_state=ai_data.get("agent_state"),
            )
        except Exception:
            logger.exception("Failed to save AI trace for session %s", request.session_id)
        return response

    except Exception as error:
        response = fallback_keyword_search_tool(db, request, error)
        try:
            trace_payload = fallback_trace_payload(response, error, request.query)
            save_ai_trace(
                db,
                request,
                response,
                current_user,
                extracted_intent=trace_payload["extracted_intent"],
                filters_applied=trace_payload["filters_applied"],
                result_restaurant_ids=trace_payload["result_restaurant_ids"],
            )
        except Exception:
            logger.exception("Failed to save fallback AI trace for session %s", request.session_id)
        return response
