# File: services/restaurant_service.py
"""
Service layer cho restaurant - chứa business logic
Xử lý: rating calculation, search logic, validation, etc.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.restaurant import Restaurant
from models.review import Review
from models.reservation import Reservation


def calculate_average_rating(db: Session, restaurant_id: UUID) -> Decimal:
    """
    Tính toán rating trung bình của restaurant từ các approved reviews
    
    Công thức: Trung bình cộng của tất cả ratings của APPROVED reviews
    """
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.restaurant_id == restaurant_id,
        Review.status == "APPROVED"
    ).scalar()
    
    if avg_rating is None:
        return Decimal("0.00")
    
    return Decimal(str(avg_rating)).quantize(Decimal("0.01"))


def update_restaurant_rating(db: Session, restaurant_id: UUID) -> Restaurant | None:
    """
    Cập nhật average_rating của restaurant
    
    Gọi hàm này mỗi khi:
    - Admin duyệt/từ chối review mới
    - Xóa review
    """
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return None
    
    new_rating = calculate_average_rating(db, restaurant_id)
    restaurant.average_rating = new_rating
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def get_restaurant_stats(db: Session, restaurant_id: UUID) -> dict:
    """
    Lấy thống kê của restaurant
    
    Return:
    {
        "total_reviews": int,
        "average_rating": Decimal,
        "total_reservations": int,
        "confirmed_reservations": int,
        "total_menu_items": int,
        "available_menu_items": int,
    }
    """
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return {}
    
    # Count reviews (approved only)
    total_reviews = db.query(Review).filter(
        Review.restaurant_id == restaurant_id,
        Review.status == "APPROVED"
    ).count()
    
    # Count reservations
    total_reservations = db.query(Reservation).filter(
        Reservation.restaurant_id == restaurant_id
    ).count()
    
    confirmed_reservations = db.query(Reservation).filter(
        Reservation.restaurant_id == restaurant_id,
        Reservation.status == "CONFIRMED"
    ).count()
    
    # Count menu items
    from models.dish import MenuItem
    total_menu_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id
    ).count()
    
    available_menu_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    ).count()
    
    return {
        "restaurant_id": str(restaurant_id),
        "average_rating": float(restaurant.average_rating),
        "total_reviews": total_reviews,
        "total_reservations": total_reservations,
        "confirmed_reservations": confirmed_reservations,
        "total_menu_items": total_menu_items,
        "available_menu_items": available_menu_items,
    }
