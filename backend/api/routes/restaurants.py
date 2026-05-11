# File: api/routes/restaurants.py
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate
from api.deps import get_current_user
from models.user import User
import crud.restaurant as crud_restaurant

router = APIRouter()


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tạo nhà hàng mới (Chỉ dành cho Owner)
    
    - Yêu cầu: Role = OWNER và Token hợp lệ
    - Status mặc định: PENDING (chờ admin duyệt)
    """
    # Chặn nếu không phải OWNER
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có Chủ nhà hàng mới được quyền tạo nhà hàng"
        )
    
    return crud_restaurant.create_restaurant(
        db=db, restaurant=restaurant, owner_id=current_user.user_id
    )


@router.get("/", response_model=List[RestaurantResponse])
def get_all_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách nhà hàng (APPROVED only)
    
    - Không cần authentication
    - Mặc định: chỉ trả về các nhà hàng đã duyệt
    """
    return crud_restaurant.get_restaurants(db=db, skip=skip, limit=limit, status="APPROVED")


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_detail(
    restaurant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết nhà hàng
    
    - Không cần authentication
    """
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại"
        )
    return restaurant


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
    # Chỉ allow owner xem của mình hoặc admin xem của ai
    if current_user.user_id != owner_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập"
        )
    
    return crud_restaurant.get_restaurants_by_owner(db, owner_id, skip, limit)


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: UUID,
    restaurant_in: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cập nhật thông tin nhà hàng
    
    - Yêu cầu: Là owner của nhà hàng đó
    """
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại"
        )
    
    # Kiểm tra quyền
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
    """
    Xóa nhà hàng
    
    - Yêu cầu: Là owner của nhà hàng đó
    """
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại"
        )
    
    # Kiểm tra quyền
    if db_restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa nhà hàng này"
        )
    
    crud_restaurant.delete_restaurant(db, restaurant_id)
    return None
