from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.reservation as crud_reservation
import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.booking import ReservationCreate, ReservationResponse
from schemas.booking import ReservationUpdate

router = APIRouter()
MIN_BOOKING_NOTICE = timedelta(minutes=30)


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can create bookings")

    reservation_time = _to_utc_naive(booking_in.reservation_time)
    minimum_time = datetime.now(timezone.utc).replace(tzinfo=None) + MIN_BOOKING_NOTICE
    if reservation_time <= minimum_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation time must be at least 30 minutes in the future",
        )

    restaurant = crud_restaurant.get_restaurant_by_id(db, booking_in.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    booking_to_create = booking_in.model_copy(update={"reservation_time": reservation_time})
    created_booking = crud_reservation.create_reservation(db, booking_to_create, current_user.user_id)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    updated_booking = crud_reservation.cancel_reservation(db, booking_id)
    return _serialize_reservation(updated_booking)


@router.put("/{booking_id}", response_model=ReservationResponse)
def update_my_booking(
    booking_id: UUID,
    booking_in: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = crud_reservation.get_reservation_by_id(db, booking_id)
    if not booking or booking.customer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be updated")

    reservation_time = _to_utc_naive(booking_in.reservation_time or booking.reservation_time)
    minimum_time = datetime.now(timezone.utc).replace(tzinfo=None) + MIN_BOOKING_NOTICE
    if reservation_time <= minimum_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation time must be at least 30 minutes in the future",
        )

    guest_count = booking_in.guest_count if booking_in.guest_count is not None else booking.guest_count
    if guest_count <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Guest count must be greater than 0")

    updated_booking = crud_reservation.update_reservation(
        db,
        booking_id,
        booking_in.model_copy(
            update={
                "reservation_time": reservation_time,
                "guest_count": guest_count,
            }
        ),
    )
    return _serialize_reservation(updated_booking)
