# File: api/routes/restaurants.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from schemas.restaurant import RestaurantCreate, RestaurantResponse
import crud.restaurant as crud_restaurant

# IMPORT TRẠM KIỂM SOÁT VÀ MODEL USER
from api.deps import get_current_user
from models.user import User 

router = APIRouter()

@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    restaurant: RestaurantCreate, 
    db: Session = Depends(get_db),
    # BẮT BUỘC PHẢI CÓ TOKEN MỚI ĐƯỢC CHẠY VÀO HÀM NÀY
    current_user: User = Depends(get_current_user) 
):
    """API Tạo nhà hàng mới (Chỉ dành cho Owner)"""
    
    # 1. Chặn nếu không phải Chủ nhà hàng
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Chỉ có Chủ nhà hàng mới được quyền tạo quán ăn"
        )
        
    # 2. Truyền current_user.id vào làm owner_id một cách tự động và bảo mật tuyệt đối
    return crud_restaurant.create_restaurant(db=db, restaurant=restaurant, owner_id=current_user.id)

# API GET (Danh sách) thì KHÔNG CẦN bảo vệ vì ai vào trang chủ cũng xem được
@router.get("/", response_model=List[RestaurantResponse])
def get_all_restaurants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_restaurant.get_restaurants(db=db, skip=skip, limit=limit)