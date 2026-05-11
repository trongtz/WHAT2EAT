# File: api/routes/favorites.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from schemas.favorite import FavoriteResponse, FavoriteCreate
from crud import favorite as crud_favorite
from crud import restaurant as crud_restaurant

router = APIRouter()

@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_restaurant(
    favorite_in: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Khách hàng thêm nhà hàng vào danh sách yêu thích"""
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Chỉ khách hàng mới có thể lưu yêu thích")
    
    restaurant = crud_restaurant.get_restaurant_by_id(db, favorite_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà hàng")
        
    # Gọi hàm is_favorite từ CRUD của bạn
    if crud_favorite.is_favorite(db, current_user.user_id, favorite_in.restaurant_id):
        raise HTTPException(status_code=409, detail="Nhà hàng đã có trong danh sách yêu thích")
        
    # Gọi hàm add_favorite từ CRUD của bạn
    return crud_favorite.add_favorite(db, favorite_in, current_user.user_id)


@router.get("/", response_model=List[FavoriteResponse])
def get_favorites(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách nhà hàng yêu thích của khách hàng"""
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Chỉ khách hàng mới có danh sách yêu thích")
    
    # Gọi hàm get_favorites_by_customer từ CRUD của bạn
    return crud_favorite.get_favorites_by_customer(db, current_user.user_id, skip=skip, limit=limit)


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa nhà hàng khỏi danh sách yêu thích"""
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Chỉ khách hàng mới có danh sách yêu thích")
        
    # Gọi hàm remove_favorite từ CRUD của bạn
    success = crud_favorite.remove_favorite(db, current_user.user_id, restaurant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu yêu thích")
    return None