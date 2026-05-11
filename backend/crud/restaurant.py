from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.restaurant import Restaurant
from schemas.restaurant import RestaurantCreate, RestaurantUpdate


def create_restaurant(db: Session, restaurant: RestaurantCreate, owner_id: UUID) -> Restaurant:
    """Tạo restaurant mới"""
    db_restaurant = Restaurant(
        **restaurant.model_dump(exclude_unset=True),
        owner_id=owner_id,
        status="PENDING"  # Mặc định chờ duyệt
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def get_restaurants(db: Session, skip: int = 0, limit: int = 100, status: str = None) -> list:
    """Lấy danh sách restaurants"""
    query = db.query(Restaurant)
    
    # Filter by status if provided
    if status:
        query = query.filter(Restaurant.status == status)
    else:
        # Mặc định chỉ lấy APPROVED restaurants
        query = query.filter(Restaurant.status == "APPROVED")
    
    return query.offset(skip).limit(limit).all()


def get_restaurant_by_id(db: Session, restaurant_id: UUID) -> Restaurant | None:
    """Lấy restaurant theo ID"""
    return db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()


def get_restaurants_by_owner(db: Session, owner_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách restaurants của một owner"""
    return db.query(Restaurant).filter(
        Restaurant.owner_id == owner_id
    ).offset(skip).limit(limit).all()


def update_restaurant(db: Session, restaurant_id: UUID, restaurant_in: RestaurantUpdate) -> Restaurant | None:
    """Cập nhật thông tin restaurant"""
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return None
    
    update_data = restaurant_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_restaurant, field, value)
    
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def delete_restaurant(db: Session, restaurant_id: UUID) -> bool:
    """Xóa restaurant"""
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return False
    
    db.delete(db_restaurant)
    db.commit()
    return True


def approve_restaurant(db: Session, restaurant_id: UUID) -> Restaurant | None:
    """Admin duyệt restaurant"""
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return None
    
    db_restaurant.status = "APPROVED"
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def reject_restaurant(db: Session, restaurant_id: UUID) -> Restaurant | None:
    """Admin từ chối restaurant"""
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return None
    
    db_restaurant.status = "REJECTED"
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant
