from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
import crud.moderation_log as crud_moderation_log
import crud.notification as crud_notification
from api.deps import get_current_user
from core.database import get_db
from models.booking import Reservation
from models.restaurant import Restaurant
from models.user import User
from schemas.moderation import ModerationLogResponse
from schemas.moderation import ModerationLogCreate
from schemas.restaurant import RestaurantAdminResponse, RestaurantResponse, RestaurantStatusUpdate
from services.capacity_service import attach_capacity_summary
from services.restaurant_service import attach_restaurant_review_summary

router = APIRouter()


def _serialize_admin_user(user: User) -> dict:
    return {
        "id": user.user_id,
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
    }


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
    pending_restaurants = db.query(Restaurant).filter(Restaurant.approval_status == "PENDING").count()
    active_restaurants = db.query(Restaurant).filter(Restaurant.approval_status == "APPROVED").count()
    total_bookings = db.query(Reservation).count()

    approved_restaurants = db.query(Restaurant).filter(Restaurant.approval_status == "APPROVED").all()
    average_rating = (
        round(
            sum(float(restaurant.rating_avg or 0) for restaurant in approved_restaurants)
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


@router.get("/users")
def get_admin_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [_serialize_admin_user(user) for user in users]


@router.put("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    if user_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot lock their own account")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.status = "BANNED" if str(user.status).upper() == "ACTIVE" else "ACTIVE"
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_admin_user(user)


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

    normalized_status = payload.normalized_status
    if normalized_status not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trạng thái hợp lệ: APPROVED hoặc REJECTED",
        )

    restaurant.approval_status = normalized_status
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    log_reason = payload.reason or ("No reason provided" if normalized_status == "REJECTED" else None)
    crud_moderation_log.create_log(
        db,
        ModerationLogCreate(
            target_type="restaurant",
            target_id=restaurant.restaurant_id,
            action="APPROVE" if normalized_status == "APPROVED" else "REJECT",
            reason=log_reason,
        ),
        current_user.user_id,
    )
    crud_notification.create_notification(
        db,
        restaurant.owner_id,
        f"RESTAURANT_{normalized_status}",
        "Restaurant moderation updated",
        f"Restaurant {restaurant.name} status changed to {normalized_status}.",
        restaurant.restaurant_id,
    )

    attach_capacity_summary(db, restaurant)
    attach_restaurant_review_summary(db, restaurant)
    return restaurant


@router.get("/moderation-logs", response_model=list[ModerationLogResponse])
def get_moderation_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    return crud_moderation_log.get_logs(db, skip=skip, limit=limit)
