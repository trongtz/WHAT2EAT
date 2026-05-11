from uuid import UUID
from sqlalchemy.orm import Session
from models.favorite import Favorite
from schemas.favorite import FavoriteCreate


def add_favorite(db: Session, favorite_in: FavoriteCreate, customer_id: UUID) -> Favorite:
    """Thêm nhà hàng vào yêu thích"""
    # Check if already exists
    existing = db.query(Favorite).filter(
        Favorite.customer_id == customer_id,
        Favorite.restaurant_id == favorite_in.restaurant_id
    ).first()
    
    if existing:
        return existing
    
    db_favorite = Favorite(
        customer_id=customer_id,
        restaurant_id=favorite_in.restaurant_id
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


def get_favorite_by_id(db: Session, favorite_id: UUID) -> Favorite | None:
    """Lấy favorite theo ID"""
    return db.query(Favorite).filter(Favorite.favorite_id == favorite_id).first()


def get_favorites_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách yêu thích của khách hàng"""
    return db.query(Favorite).filter(
        Favorite.customer_id == customer_id
    ).offset(skip).limit(limit).all()


def is_favorite(db: Session, customer_id: UUID, restaurant_id: UUID) -> bool:
    """Kiểm tra xem nhà hàng có trong yêu thích không"""
    return db.query(Favorite).filter(
        Favorite.customer_id == customer_id,
        Favorite.restaurant_id == restaurant_id
    ).first() is not None


def remove_favorite(db: Session, customer_id: UUID, restaurant_id: UUID) -> bool:
    """Xóa nhà hàng khỏi yêu thích"""
    db_favorite = db.query(Favorite).filter(
        Favorite.customer_id == customer_id,
        Favorite.restaurant_id == restaurant_id
    ).first()
    
    if not db_favorite:
        return False
    
    db.delete(db_favorite)
    db.commit()
    return True
