from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from models.booking import Reservation
from models.checkin import CheckIn
from schemas.checkin import CheckInCreate


def create_checkin(db: Session, payload: CheckInCreate, customer_id: UUID) -> CheckIn:
    is_verified = False
    if payload.reservation_id:
        reservation = (
            db.query(Reservation)
            .filter(
                Reservation.reservation_id == payload.reservation_id,
                Reservation.customer_id == customer_id,
                Reservation.restaurant_id == payload.restaurant_id,
                Reservation.status == "CONFIRMED",
            )
            .first()
        )
        is_verified = reservation is not None

    checkin = CheckIn(
        customer_id=customer_id,
        is_verified=is_verified,
        **payload.model_dump(),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def get_checkin_by_reservation(db: Session, reservation_id: UUID) -> Optional[CheckIn]:
    return db.query(CheckIn).filter(CheckIn.reservation_id == reservation_id).first()


def create_verified_checkin_from_reservation(
    db: Session,
    reservation: Reservation,
    *,
    crowd_status: Optional[str] = None,
    note: Optional[str] = None,
) -> CheckIn:
    existing = get_checkin_by_reservation(db, reservation.reservation_id)
    if existing:
        return existing

    checkin = CheckIn(
        customer_id=reservation.customer_id,
        restaurant_id=reservation.restaurant_id,
        reservation_id=reservation.reservation_id,
        crowd_status=crowd_status,
        note=note,
        is_verified=True,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def get_checkins_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 100) -> list[CheckIn]:
    return (
        db.query(CheckIn)
        .filter(CheckIn.customer_id == customer_id)
        .order_by(CheckIn.checkin_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_checkins_by_restaurant(db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100) -> list[CheckIn]:
    return (
        db.query(CheckIn)
        .filter(CheckIn.restaurant_id == restaurant_id)
        .order_by(CheckIn.checkin_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
