from sqlalchemy.orm import Session
from models.restaurant import Restaurant
from schemas.restaurant import RestaurantCreate

def create_restaurant(db: Session, restaurant: RestaurantCreate, owner_id: int):
    # .model_dump() tự động chuyển Pydantic model thành Dictionary
    # db_restaurant = Restaurant(**restaurant.model_dump())
    db_restaurant = Restaurant(**restaurant.model_dump(), owner_id=owner_id)
    
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    
    return db_restaurant

def get_restaurants(db: Session, skip: int = 0, limit: int = 100):
    # Hàm lấy danh sách nhà hàng (có phân trang cơ bản)
    return db.query(Restaurant).offset(skip).limit(limit).all()