from uuid import UUID
from sqlalchemy.orm import Session
from models.booking import Reservation
from schemas.booking import ReservationCreate, ReservationUpdate


def create_reservation(db: Session, reservation_in: ReservationCreate, customer_id: UUID) -> Reservation:
    """Tạo reservation mới"""
    db_reservation = Reservation(
        **reservation_in.model_dump(exclude_unset=True),
        customer_id=customer_id,
        status="PENDING"
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def get_reservation_by_id(db: Session, reservation_id: UUID) -> Reservation | None:
    """Lấy reservation theo ID"""
    return db.query(Reservation).filter(Reservation.reservation_id == reservation_id).first()


def get_reservations_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách reservations của khách hàng"""
    return db.query(Reservation).filter(
        Reservation.customer_id == customer_id
    ).offset(skip).limit(limit).all()


def get_reservations_by_restaurant(db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách reservations của nhà hàng"""
    return db.query(Reservation).filter(
        Reservation.restaurant_id == restaurant_id
    ).offset(skip).limit(limit).all()


def update_reservation(db: Session, reservation_id: UUID, reservation_in: ReservationUpdate) -> Reservation | None:
    """Cập nhật reservation"""
    db_reservation = get_reservation_by_id(db, reservation_id)
    if not db_reservation:
        return None
    
    update_data = reservation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reservation, field, value)
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def cancel_reservation(db: Session, reservation_id: UUID) -> Reservation | None:
    """Hủy reservation"""
    db_reservation = get_reservation_by_id(db, reservation_id)
    if not db_reservation:
        return None
    
    if db_reservation.status == "CANCELLED":
        return db_reservation
    
    db_reservation.status = "CANCELLED"
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def confirm_reservation(db: Session, reservation_id: UUID) -> Reservation | None:
    """Owner xác nhận reservation"""
    db_reservation = get_reservation_by_id(db, reservation_id)
    if not db_reservation:
        return None
    
    db_reservation.status = "CONFIRMED"
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def reject_reservation(db: Session, reservation_id: UUID, rejection_reason: str) -> Reservation | None:
    """Owner từ chối reservation"""
    db_reservation = get_reservation_by_id(db, reservation_id)
    if not db_reservation:
        return None
    
    db_reservation.status = "REJECTED"
    db_reservation.rejection_reason = rejection_reason
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation
