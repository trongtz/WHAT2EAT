from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.reservation as crud_reservation
import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.booking import ReservationCreate, ReservationResponse
from services.capacity_service import get_available_capacity_for_slot

router = APIRouter()


def normalize_status_label(status_value: str) -> str:
    mapping = {
        "PENDING": "Chờ duyệt",
        "CONFIRMED": "Đã xác nhận",
        "REJECTED": "Từ chối",
        "CANCELLED": "Đã hủy",
    }
    return mapping.get(status_value, status_value)


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ khách hàng mới có thể đặt bàn",
        )

    restaurant = crud_restaurant.get_restaurant_by_id(db, booking_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng phù hợp")

    available_capacity = get_available_capacity_for_slot(db, booking_in.restaurant_id, booking_in.reservation_time)
    if available_capacity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Khung giờ này đã hết bàn trống",
        )

    return crud_reservation.create_reservation(db=db, reservation_in=booking_in, customer_id=current_user.user_id)


@router.get("/my-bookings", response_model=List[ReservationResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_reservation.get_reservations_by_customer(db, customer_id=current_user.user_id)
