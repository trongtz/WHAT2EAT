from sqlalchemy.orm import Session
from models.booking import Booking
from schemas.booking import BookingCreate

def create_booking(db: Session, booking: BookingCreate, customer_id: int):
    # Ghép dữ liệu từ form Frontend với customer_id (lấy từ Token)
    db_booking = Booking(**booking.model_dump(), customer_id=customer_id)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_bookings_by_customer(db: Session, customer_id: int):
    # Lấy lịch sử đặt bàn của một khách hàng cụ体
    return db.query(Booking).filter(Booking.customer_id == customer_id).all()

def get_bookings_by_restaurant(db: Session, restaurant_id: int):
    # Lấy danh sách đặt bàn của một nhà hàng cụ thể
    return db.query(Booking).filter(Booking.restaurant_id == restaurant_id).all()

def update_booking_status(db: Session, booking_id: int, status: str):
    # Cập nhật trạng thái đơn đặt bàn (pending -> confirmed/cancelled)
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        booking.status = status
        db.commit()
        db.refresh(booking)
    return booking