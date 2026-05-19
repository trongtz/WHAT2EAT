from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.reservation as crud_reservation
import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.booking import ReservationCreate, ReservationResponse

router = APIRouter()


def _serialize_reservation(reservation):
    return {
        "reservation_id": reservation.reservation_id,
        "restaurant_id": reservation.restaurant_id,
        "customer_id": reservation.customer_id,
        "reservation_time": reservation.reservation_time,
        "guest_count": reservation.guest_count,
        "notes": reservation.notes,
        "status": reservation.status,
        "rejection_reason": reservation.rejection_reason,
        "created_at": reservation.created_at,
        "updated_at": reservation.updated_at,
    }


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ khách hàng mới được đặt bàn")

    restaurant = crud_restaurant.get_restaurant_by_id(db, booking_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng này")

    created_booking = crud_reservation.create_reservation(db, booking_in, current_user.user_id)
    return _serialize_reservation(created_booking)


@router.get("/my-bookings", response_model=list[ReservationResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bookings = crud_reservation.get_reservations_by_customer(db, current_user.user_id)
    return [_serialize_reservation(booking) for booking in bookings]


@router.put("/{booking_id}/cancel", response_model=ReservationResponse)
def cancel_my_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = crud_reservation.get_reservation_by_id(db, booking_id)
    if not booking or booking.customer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn đặt bàn")

    updated_booking = crud_reservation.cancel_reservation(db, booking_id)
    return _serialize_reservation(updated_booking)
