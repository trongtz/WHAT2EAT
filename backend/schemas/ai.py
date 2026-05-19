# File: schemas/ai.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# 1. Dữ liệu Frontend gửi lên Backend
class AIRecommendationRequest(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# 2. Dữ liệu một nhà hàng mà AI trả về
class AIRestaurantMatch(BaseModel):
    id: str 
    name: str
    address: str
    distance_km: Optional[float] = None
    match_score: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

# 3. Dữ liệu Backend trả về cho Frontend
class AIRecommendationResponse(BaseModel):
    message: str # Câu chào của AI
    total_found: int
    recommended_restaurants: List[AIRestaurantMatch]