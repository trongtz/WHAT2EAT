from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.booking import Reservation
from models.restaurant import Restaurant
from models.review import Review
from models.user import User

router = APIRouter()

VALID_BOOKING_STATUSES = {"PENDING", "CONFIRMED", "REJECTED", "CANCELLED", "COMPLETED"}


class OwnerBookingStatusUpdate(BaseModel):
    bookingId: UUID
    status: str


def require_owner(current_user: User) -> None:
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhà hàng mới có quyền thực hiện thao tác này",
        )


def normalize_booking_status(status_value: str) -> str:
    raw = (status_value or "").strip().upper()
    mapping = {
        "ĐÃ XÁC NHẬN": "CONFIRMED",
        "DA XAC NHAN": "CONFIRMED",
        "CONFIRMED": "CONFIRMED",
        "CHỜ DUYỆT": "PENDING",
        "CHO DUYET": "PENDING",
        "PENDING": "PENDING",
        "ĐÃ HỦY": "CANCELLED",
        "DA HUY": "CANCELLED",
        "CANCELLED": "CANCELLED",
        "TỪ CHỐI": "REJECTED",
        "TU CHOI": "REJECTED",
        "REJECTED": "REJECTED",
        "COMPLETED": "COMPLETED",
    }
    return mapping.get(raw, raw)


def get_owner_restaurant_ids(db: Session, owner_id: UUID) -> list[UUID]:
    rows = (
        db.query(Restaurant.restaurant_id)
        .filter(Restaurant.owner_id == owner_id)
        .all()
    )
    return [row[0] for row in rows]


def serialize_owner_booking(reservation: Reservation) -> dict:
    return {
        "id": reservation.reservation_id,
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
        "customerName": reservation.customer.full_name if reservation.customer else "Khách hàng",
    }


@router.get("/reviews")
def get_owner_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(current_user)

    restaurant_ids = get_owner_restaurant_ids(db, current_user.user_id)
    if not restaurant_ids:
        return []

    reviews = (
        db.query(Review)
        .filter(
            Review.restaurant_id.in_(restaurant_ids),
            Review.status != "REJECTED",
        )
        .order_by(Review.created_at.desc())
        .all()
    )

    return [
        {
            "id": review.review_id,
            "review_id": review.review_id,
            "restaurant_id": review.restaurant_id,
            "restaurant_name": review.restaurant.name if review.restaurant else "Nhà hàng",
            "customer_id": review.customer_id,
            "rating": review.rating,
            "comment": review.comment,
            "status": review.status,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "userName": review.customer.full_name if review.customer else "Khách hàng",
        }
        for review in reviews
    ]


@router.get("/bookings")
def get_owner_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(current_user)

    restaurant_ids = get_owner_restaurant_ids(db, current_user.user_id)
    if not restaurant_ids:
        return []

    reservations = (
        db.query(Reservation)
        .filter(Reservation.restaurant_id.in_(restaurant_ids))
        .order_by(Reservation.reservation_time.desc())
        .all()
    )

    return [serialize_owner_booking(reservation) for reservation in reservations]


@router.post("/bookings/update-status")
def update_owner_booking_status(
    payload: OwnerBookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(current_user)

    reservation = (
        db.query(Reservation)
        .join(Restaurant, Restaurant.restaurant_id == Reservation.restaurant_id)
        .filter(
            Reservation.reservation_id == payload.bookingId,
            Restaurant.owner_id == current_user.user_id,
        )
        .first()
    )
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn đặt bàn")

    next_status = normalize_booking_status(payload.status)
    if next_status not in VALID_BOOKING_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái đặt bàn không hợp lệ")

    reservation.status = next_status
    if next_status != "REJECTED":
        reservation.rejection_reason = None

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return serialize_owner_booking(reservation)
