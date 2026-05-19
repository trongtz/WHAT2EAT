# File: api/routes/ai.py
from fastapi import APIRouter, HTTPException
from schemas.ai import AIRecommendationRequest, AIRecommendationResponse, AIRestaurantMatch
import httpx # Thư viện gọi API (cài đặt: pip install httpx)

router = APIRouter()

@router.post("/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendation(request: AIRecommendationRequest):
    try:
        # 1. Chuẩn bị payload
        ai_service_payload = {
            "query": request.query,
            "latitude": request.latitude,
            "longitude": request.longitude
        }

        # 2. Gọi sang API
        # Nếu code AI nằm trong cùng project, bạn chỉ cần gọi hàm thay vì gọi HTTP
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                "http://127.0.0.1:8001/api/ai/process", # Đổi URL này theo máy đồng đội
                json=ai_service_payload,
                timeout=15.0
            )
            ai_response.raise_for_status()
            ai_data = ai_response.json() # Đây chính là cục JSON bạn vừa gửi cho mình!

        # 3. Bóc tách dữ liệu JSON của đồng đội và Map vào Schema của bạn
        ai_restaurants = ai_data.get("restaurants", [])
        total = ai_data.get("total", 0)
        
        # 4. Trả về kết quả đẹp đẽ cho Frontend
        return AIRecommendationResponse(
            message=f"Mình tìm thấy {total} quán cà phê ấm cúng gần bạn nhất nhé!",
            total_found=total,
            recommended_restaurants=[
                AIRestaurantMatch(
                    id=r["id"],
                    name=r["name"],
                    address=r["address"],
                    distance_km=r["distance_km"],
                    match_score=r["match_score"]
                ) for r in ai_restaurants
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối AI Service: {str(e)}")