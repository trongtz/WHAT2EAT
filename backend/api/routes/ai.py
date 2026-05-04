from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse
from services import ai_service # Nhúng chiếc hộp của AI Engineer vào

router = APIRouter()

@router.post("/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendations(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db)
):
    """API Giao tiếp chính với Frontend"""
    
    # 1. Giao việc cho AI Service xử lý
    ai_result = ai_service.generate_recommendation(query=request.query, db=db)
    
    # 2. Lấy kết quả từ AI Service trả về chuẩn định dạng Schema cho Frontend
    return AIRecommendationResponse(
        message=ai_result["message"],
        recommended_restaurants=ai_result["restaurants"]
    )