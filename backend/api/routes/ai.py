from uuid import UUID

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud.ai_chat as crud_ai_chat
import crud.restaurant as crud_restaurant
from api.deps import get_optional_current_user
from core.database import get_db
from models.user import User
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse, AIRestaurantMatch
from schemas.ai_chat import AIChatMessageCreate, RecommendationLogCreate

router = APIRouter()


def _restaurant_to_ai_match(restaurant) -> AIRestaurantMatch:
    return AIRestaurantMatch(
        id=str(restaurant.restaurant_id),
        name=restaurant.name,
        address=restaurant.address,
        distance_km=None,
        match_score=max(0.0, min(1.0, float(restaurant.average_rating or 0) / 5)),
        reason="Fallback keyword search result",
    )


def _save_ai_trace(
    db: Session,
    request: AIRecommendationRequest,
    response: AIRecommendationResponse,
    current_user: User | None,
) -> None:
    if not request.session_id:
        return

    session = crud_ai_chat.get_session(db, request.session_id)
    if not session:
        return

    crud_ai_chat.create_message(
        db,
        request.session_id,
        AIChatMessageCreate(role="user", content=request.query, processing_status="SUCCESS"),
    )
    crud_ai_chat.create_message(
        db,
        request.session_id,
        AIChatMessageCreate(role="assistant", content=response.message, processing_status="SUCCESS"),
    )

    for index, restaurant in enumerate(response.recommended_restaurants, start=1):
        try:
            restaurant_id = UUID(str(restaurant.id))
        except ValueError:
            continue

        crud_ai_chat.create_recommendation_log(
            db,
            RecommendationLogCreate(
                session_id=request.session_id,
                customer_id=current_user.user_id if current_user else None,
                restaurant_id=restaurant_id,
                score=restaurant.match_score,
                reason=restaurant.reason,
                source=response.source,
                rank_position=index,
                prompt_summary=request.query,
            ),
        )


@router.post("/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendation(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    try:
        ai_service_payload = {
            "query": request.query,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "session_id": str(request.session_id) if request.session_id else None,
        }

        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                "http://127.0.0.1:8001/api/ai/process",
                json=ai_service_payload,
                timeout=15.0,
            )
            ai_response.raise_for_status()
            ai_data = ai_response.json()

        ai_restaurants = ai_data.get("restaurants", [])
        response = AIRecommendationResponse(
            message=ai_data.get("message") or f"Tim thay {len(ai_restaurants)} nha hang phu hop.",
            total_found=ai_data.get("total", len(ai_restaurants)),
            recommended_restaurants=[
                AIRestaurantMatch(
                    id=str(restaurant["id"]),
                    name=restaurant["name"],
                    address=restaurant["address"],
                    distance_km=restaurant.get("distance_km"),
                    match_score=restaurant.get("match_score"),
                    reason=restaurant.get("reason"),
                )
                for restaurant in ai_restaurants
            ],
            session_id=request.session_id,
            source="AI",
        )
        _save_ai_trace(db, request, response, current_user)
        return response

    except Exception:
        restaurants = crud_restaurant.search_restaurants(db, query=request.query, limit=5)
        matches = [_restaurant_to_ai_match(restaurant) for restaurant in restaurants]
        response = AIRecommendationResponse(
            message="AI Assistant hien chua phan hoi duoc. He thong da chuyen sang tim kiem co ban.",
            total_found=len(matches),
            recommended_restaurants=matches,
            session_id=request.session_id,
            source="FALLBACK",
        )
        _save_ai_trace(db, request, response, current_user)
        return response
