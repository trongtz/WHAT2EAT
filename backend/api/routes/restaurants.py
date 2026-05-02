from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_restaurants():
    """API lấy danh sách nhà hàng: /api/restaurants"""
    return {"message": "Danh sách nhà hàng"}

@router.get("/{id}")
async def get_restaurant_detail(id: int):
    """API chi tiết nhà hàng: /api/restaurants/{id}"""
    return {"message": f"Chi tiết nhà hàng {id}"}