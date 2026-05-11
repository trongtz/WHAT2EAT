from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
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


def search_restaurants(
    db: Session,
    query: str = None,
    cuisine_type: str = None,
    price_range: str = None,
    min_rating: Decimal = None,
    skip: int = 0,
    limit: int = 100,
) -> list:
    """
    Tìm kiếm restaurants với filters
    
    - query: tìm theo tên hoặc địa chỉ (case-insensitive)
    - cuisine_type: lọc theo loại ẩm thực
    - price_range: "cheap", "mid", "expensive"
    - min_rating: rating tối thiểu
    - Mặc định chỉ APPROVED restaurants
    """
    base_query = db.query(Restaurant).filter(Restaurant.status == "APPROVED")
    
    # Search by name or address
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Restaurant.name.ilike(search_term),
                Restaurant.address.ilike(search_term)
            )
        )
    
    # Filter by cuisine type
    if cuisine_type:
        base_query = base_query.filter(Restaurant.cuisine_type == cuisine_type)
    
    # Filter by price range
    if price_range and price_range in ["cheap", "mid", "expensive"]:
        base_query = base_query.filter(Restaurant.price_range == price_range)
    
    # Filter by minimum rating
    if min_rating is not None:
        base_query = base_query.filter(Restaurant.average_rating >= min_rating)
    
    return base_query.offset(skip).limit(limit).all()


def search_by_location(
    db: Session,
    latitude: Decimal,
    longitude: Decimal,
    radius_km: float = 5.0,  # Mặc định: 5km
    skip: int = 0,
    limit: int = 100,
) -> list:
    """
    Tìm restaurants gần vị trí (tính khoảng cách Haversine - simplified version)
    
    Note: Để performance tốt hơn, nên dùng PostGIS extension sau này.
    Hiện tại dùng phương pháp đơn giản: lọc bounding box rồi tính khoảng cách.
    
    Công thức tính: ~1 degree ≈ 111 km
    """
    # Bounding box: ±(radius_km / 111)
    lat_delta = Decimal(radius_km / 111)
    lon_delta = Decimal(radius_km / 111)
    
    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta
    
    # Filter by bounding box
    restaurants = db.query(Restaurant).filter(
        Restaurant.status == "APPROVED",
        Restaurant.latitude.isnot(None),
        Restaurant.longitude.isnot(None),
        Restaurant.latitude >= min_lat,
        Restaurant.latitude <= max_lat,
        Restaurant.longitude >= min_lon,
        Restaurant.longitude <= max_lon,
    ).offset(skip).limit(limit).all()
    
    return restaurants


def get_popular_restaurants(db: Session, limit: int = 10) -> list:
    """Lấy nhà hàng được đánh giá cao nhất"""
    return db.query(Restaurant).filter(
        Restaurant.status == "APPROVED"
    ).order_by(Restaurant.average_rating.desc()).limit(limit).all()


def get_newly_added_restaurants(db: Session, limit: int = 10) -> list:
    """Lấy nhà hàng mới được thêm"""
    return db.query(Restaurant).filter(
        Restaurant.status == "APPROVED"
    ).order_by(Restaurant.created_at.desc()).limit(limit).all()

