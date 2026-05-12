from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.booking import Reservation
from models.restaurant import Restaurant
from models.user import User
from schemas.restaurant import RestaurantAdminResponse, RestaurantResponse, RestaurantStatusUpdate
from services.capacity_service import attach_capacity_summary
from services.restaurant_service import attach_restaurant_review_summary

router = APIRouter()


def require_admin(current_user: User) -> None:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền thực hiện thao tác này",
        )


@router.get("/overview")
def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    total_users = db.query(User).count()
    total_owners = db.query(User).filter(User.role == "OWNER").count()
    total_customers = db.query(User).filter(User.role == "CUSTOMER").count()
    total_restaurants = db.query(Restaurant).count()
    pending_restaurants = db.query(Restaurant).filter(Restaurant.status == "PENDING").count()
    active_restaurants = db.query(Restaurant).filter(Restaurant.status == "APPROVED").count()
    total_bookings = db.query(Reservation).count()

    approved_restaurants = db.query(Restaurant).filter(Restaurant.status == "APPROVED").all()
    average_rating = (
        round(
            sum(float(restaurant.average_rating or 0) for restaurant in approved_restaurants)
            / len(approved_restaurants),
            1,
        )
        if approved_restaurants
        else 0
    )

    return {
        "totalUsers": total_users,
        "totalOwners": total_owners,
        "totalCustomers": total_customers,
        "totalRestaurants": total_restaurants,
        "pendingRestaurants": pending_restaurants,
        "activeRestaurants": active_restaurants,
        "totalBookings": total_bookings,
        "averageRating": average_rating,
    }


@router.get("/restaurants", response_model=list[RestaurantAdminResponse])
def get_admin_restaurants(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    restaurants = crud_restaurant.get_restaurants(db, skip=skip, limit=limit, status=status_filter)
    if not status_filter:
        restaurants = db.query(Restaurant).offset(skip).limit(limit).all()

    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
        setattr(restaurant, "owner_name", restaurant.owner.full_name if restaurant.owner else "")
        setattr(restaurant, "owner_email", restaurant.owner.email if restaurant.owner else "")

    return restaurants


@router.put("/restaurants/{restaurant_id}/status", response_model=RestaurantResponse)
def update_restaurant_status(
    restaurant_id: UUID,
    payload: RestaurantStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    normalized_status = (payload.status or "").strip().upper()
    if normalized_status not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trạng thái hợp lệ: APPROVED hoặc REJECTED",
        )

    restaurant.status = normalized_status
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    attach_capacity_summary(db, restaurant)
    attach_restaurant_review_summary(db, restaurant)
    return restaurant
