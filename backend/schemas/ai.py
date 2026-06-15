from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AIRecommendationRequest(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    session_id: Optional[UUID] = None


class AIRestaurantMatch(BaseModel):
    id: str
    name: str
    address: str
    images: Optional[list[str]] = None
    image: Optional[str] = None
    average_rating: Optional[float] = None
    distance_km: Optional[float] = None
    match_score: Optional[float] = None
    reason: Optional[str] = None
    available_capacity: Optional[int] = None
    quality_score: Optional[float] = None
    availability_score: Optional[float] = None
    quality_signals: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class AIRecommendationResponse(BaseModel):
    message: str
    total_found: int
    recommended_restaurants: List[AIRestaurantMatch]
    session_id: Optional[UUID] = None
    source: str = "AI"
    agent: Optional[dict[str, Any]] = None
    booking: Optional[dict[str, Any]] = None
