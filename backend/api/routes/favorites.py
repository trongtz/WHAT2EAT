from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from crud import favorite as crud_favorite
from crud import restaurant as crud_restaurant
from models.user import User
from schemas.favorite import FavoriteCreate, FavoriteResponse, FavoriteToggleResponse
from schemas.restaurant import RestaurantResponse
from services.capacity_service import attach_capacity_summary
from services.restaurant_service import attach_restaurant_review_summary

router = APIRouter()


def require_customer(current_user: User) -> None:
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ khách hàng mới có thể dùng danh sách yêu thích",
        )


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_restaurant(
    favorite_in: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    restaurant = crud_restaurant.get_restaurant_by_id(db, favorite_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng")

    if crud_favorite.is_favorite(db, current_user.user_id, favorite_in.restaurant_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nhà hàng đã có trong yêu thích")

    return crud_favorite.add_favorite(db, favorite_in, current_user.user_id)


@router.post("/toggle", response_model=FavoriteToggleResponse)
def toggle_favorite_restaurant(
    favorite_in: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    restaurant = crud_restaurant.get_restaurant_by_id(db, favorite_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng")

    if crud_favorite.is_favorite(db, current_user.user_id, favorite_in.restaurant_id):
        crud_favorite.remove_favorite(db, current_user.user_id, favorite_in.restaurant_id)
        return FavoriteToggleResponse(restaurant_id=favorite_in.restaurant_id, is_favorite=False)

    crud_favorite.add_favorite(db, favorite_in, current_user.user_id)
    return FavoriteToggleResponse(restaurant_id=favorite_in.restaurant_id, is_favorite=True)


@router.get("/", response_model=List[FavoriteResponse])
def get_favorites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)
    return crud_favorite.get_favorites_by_customer(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/restaurants", response_model=List[RestaurantResponse])
def get_favorite_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)
    restaurants = crud_favorite.get_favorite_restaurants_by_customer(db, current_user.user_id, skip=skip, limit=limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    success = crud_favorite.remove_favorite(db, current_user.user_id, restaurant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy dữ liệu yêu thích")
    return None
