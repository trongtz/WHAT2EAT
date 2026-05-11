# File: api/routes/restaurants.py
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate
from schemas.dish import MenuItemResponse    # Thêm schema cho Menu
from schemas.review import ReviewResponse    # Thêm schema cho Review
from api.deps import get_current_user
from models.user import User

import crud.restaurant as crud_restaurant
import crud.menu_item as crud_menu_item      # Thêm crud cho Menu
import crud.review as crud_review            # Thêm crud cho Review

router = APIRouter()

# ---------------------------------------------------------
# 1. NHÓM TÌM KIẾM & KHÁM PHÁ (Phải đặt trên /{restaurant_id})
# ---------------------------------------------------------

@router.get("/search", response_model=List[RestaurantResponse])
def search_restaurants(
    query: Optional[str] = Query(None, description="Tìm theo tên hoặc địa chỉ"),
    cuisine_type: Optional[str] = Query(None, description="Loại ẩm thực"),
    price_range: Optional[str] = Query(None, description="cheap, mid, expensive"),
    min_rating: Optional[Decimal] = Query(None, description="Rating tối thiểu"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Tìm kiếm và lọc nhà hàng
    - Mặc định chỉ trả về nhà hàng đã APPROVED
    """
    return crud_restaurant.search_restaurants(db, query, cuisine_type, price_range, min_rating, skip, limit)


@router.get("/nearby", response_model=List[RestaurantResponse])
def get_nearby_restaurants(
    latitude: Decimal = Query(..., description="Vĩ độ hiện tại"),
    longitude: Decimal = Query(..., description="Kinh độ hiện tại"),
    radius_km: float = Query(5.0, description="Bán kính tìm kiếm (km)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Tìm nhà hàng gần đây dựa trên tọa độ GPS"""
    return crud_restaurant.search_by_location(db, latitude, longitude, radius_km, skip, limit)


@router.get("/popular", response_model=List[RestaurantResponse])
def get_popular_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    """Lấy danh sách nhà hàng có điểm đánh giá cao nhất"""
    return crud_restaurant.get_popular_restaurants(db, limit)


@router.get("/new", response_model=List[RestaurantResponse])
def get_new_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    """Lấy danh sách nhà hàng mới được duyệt"""
    return crud_restaurant.get_newly_added_restaurants(db, limit)


@router.get("/", response_model=List[RestaurantResponse])
def get_all_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách nhà hàng (APPROVED only)
    - Không cần authentication
    """
    return crud_restaurant.get_restaurants(db=db, skip=skip, limit=limit, status="APPROVED")


@router.get("/owner/{owner_id}", response_model=List[RestaurantResponse])
def get_owner_restaurants(
    owner_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách nhà hàng của một owner
    - Yêu cầu: Là owner đó hoặc admin
    """
    if current_user.user_id != owner_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập"
        )
    return crud_restaurant.get_restaurants_by_owner(db, owner_id, skip, limit)


# ---------------------------------------------------------
# 2. NHÓM CHI TIẾT & QUẢN LÝ (Chứa path parameter /{restaurant_id})
# ---------------------------------------------------------

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_detail(
    restaurant_id: UUID,
    db: Session = Depends(get_db)
):
    """Lấy thông tin chi tiết nhà hàng"""
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại hoặc chưa được duyệt"
        )
    return restaurant


@router.get("/{restaurant_id}/menu", response_model=List[MenuItemResponse])
def get_restaurant_menu(
    restaurant_id: UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Lấy danh sách thực đơn của nhà hàng"""
    return crud_menu_item.get_by_restaurant(db, restaurant_id, skip=skip, limit=limit)


@router.get("/{restaurant_id}/reviews", response_model=List[ReviewResponse])
def get_restaurant_reviews(
    restaurant_id: UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Lấy danh sách các đánh giá đã được duyệt của nhà hàng"""
    return crud_review.get_reviews_by_restaurant(db, restaurant_id, skip=skip, limit=limit)


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tạo nhà hàng mới (Chỉ dành cho Owner)"""
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có Chủ nhà hàng mới được quyền tạo nhà hàng"
        )
    return crud_restaurant.create_restaurant(
        db=db, restaurant=restaurant, owner_id=current_user.user_id
    )


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: UUID,
    restaurant_in: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin nhà hàng (Yêu cầu: Là owner của nhà hàng)"""
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại"
        )
    
    if db_restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật nhà hàng này"
        )
    return crud_restaurant.update_restaurant(db, restaurant_id, restaurant_in)


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa nhà hàng (Yêu cầu: Là owner của nhà hàng)"""
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại"
        )
    
    if db_restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa nhà hàng này"
        )
    crud_restaurant.delete_restaurant(db, restaurant_id)
    return None