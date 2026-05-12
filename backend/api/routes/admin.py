from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.restaurant import RestaurantAdminResponse, RestaurantStatusUpdate
from services.capacity_service import attach_capacity_summary
from services.restaurant_service import attach_restaurant_review_summary

router = APIRouter()


def require_admin(current_user: User) -> None:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền thực hiện thao tác này",
        )


@router.get("/restaurants", response_model=List[RestaurantAdminResponse])
def get_admin_restaurants(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    normalized_status = status_filter.upper() if isinstance(status_filter, str) else None
    restaurants = crud_restaurant.get_restaurants_for_admin(db, normalized_status, skip, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/restaurants/pending", response_model=List[RestaurantAdminResponse])
def get_pending_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    restaurants = crud_restaurant.get_restaurants_for_admin(db, "PENDING", skip, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.put("/restaurants/{restaurant_id}/status", response_model=RestaurantAdminResponse)
def update_restaurant_status(
    restaurant_id: UUID,
    payload: RestaurantStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    normalized_status = payload.status.upper()

    if normalized_status == "APPROVED":
        restaurant = crud_restaurant.approve_restaurant(db, restaurant_id)
    elif normalized_status == "REJECTED":
        restaurant = crud_restaurant.reject_restaurant(db, restaurant_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trạng thái hợp lệ: APPROVED hoặc REJECTED",
        )

    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    owner = restaurant.owner
    setattr(restaurant, "owner_name", owner.full_name if owner else None)
    setattr(restaurant, "owner_email", owner.email if owner else None)
    attach_capacity_summary(db, restaurant)
    attach_restaurant_review_summary(db, restaurant)
    return restaurant
