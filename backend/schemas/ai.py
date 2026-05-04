# File: schemas/ai.py
from pydantic import BaseModel
from typing import List, Optional
from schemas.restaurant import RestaurantResponse

class AIRecommendationRequest(BaseModel):
    query: str # Ví dụ: "Tìm quán cafe yên tĩnh để làm việc quận 1"

class AIRecommendationResponse(BaseModel):
    message: str # Câu trả lời tự nhiên của AI (VD: "Dạ, em tìm thấy vài quán yên tĩnh cho mình đây ạ")
    recommended_restaurants: List[RestaurantResponse] # Danh sách nhà hàng phù hợp