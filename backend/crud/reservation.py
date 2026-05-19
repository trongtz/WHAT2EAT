from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
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


def count_available_seats(
    db: Session,
    restaurant_id: UUID,
    reservation_time: datetime,
    max_capacity: int
) -> int:
    """
    Tính số ghế còn trống cho một khung giờ cụ thể
    
    Logic:
    1. Lấy max_capacity từ Capacity/CapacityOverride
    2. Tính tổng guest_count từ các CONFIRMED/PENDING reservations
    3. Return max_capacity - tổng_booked
    """
    # Count confirmed + pending reservations for this time slot
    # Simplified: count all non-rejected reservations
    booked_seats = db.query(func.sum(Reservation.guest_count)).filter(
        Reservation.restaurant_id == restaurant_id,
        Reservation.reservation_time == reservation_time,
        Reservation.status.in_(["CONFIRMED", "PENDING"])
    ).scalar() or 0
    
    available = max_capacity - int(booked_seats)
    return max(0, available)


def check_overbooking(
    db: Session,
    restaurant_id: UUID,
    reservation_time: datetime,
    guest_count: int,
    max_capacity: int
) -> bool:
    """
    Kiểm tra xem reservation này có gây overbooking không
    
    Return: True nếu OK (không overbooking), False nếu vượt quá
    """
    available = count_available_seats(db, restaurant_id, reservation_time, max_capacity)
    return guest_count <= available

