from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.restaurant import Restaurant
from schemas.restaurant import RestaurantCreate, RestaurantUpdate


def create_restaurant(db: Session, restaurant: RestaurantCreate, owner_id: UUID) -> Restaurant:
    restaurant_data = restaurant.model_dump(exclude_unset=True)
    restaurant_data.pop("max_capacity", None)
    db_restaurant = Restaurant(
        **restaurant_data,
        owner_id=owner_id,
        status="PENDING",
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def get_restaurants(db: Session, skip: int = 0, limit: int = 100, status: str | None = None) -> list:
    query = db.query(Restaurant)
    if status:
        query = query.filter(Restaurant.status == status)
    else:
        query = query.filter(Restaurant.status == "APPROVED")
    return query.offset(skip).limit(limit).all()


def get_restaurant_by_id(db: Session, restaurant_id: UUID) -> Restaurant | None:
    return db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()


def get_restaurants_by_owner(db: Session, owner_id: UUID, skip: int = 0, limit: int = 100) -> list:
    return (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_restaurant(db: Session, restaurant_id: UUID, restaurant_in: RestaurantUpdate) -> Restaurant | None:
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return None

    update_data = restaurant_in.model_dump(exclude_unset=True)
    update_data.pop("max_capacity", None)
    for field, value in update_data.items():
        setattr(db_restaurant, field, value)

    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def delete_restaurant(db: Session, restaurant_id: UUID) -> bool:
    db_restaurant = get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        return False

    db.delete(db_restaurant)
    db.commit()
    return True


def search_restaurants(
    db: Session,
    query: str | None = None,
    cuisine_type: str | None = None,
    price_range: str | None = None,
    min_rating: Decimal | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list:
    base_query = db.query(Restaurant).filter(Restaurant.status == "APPROVED")

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Restaurant.name.ilike(search_term),
                Restaurant.address.ilike(search_term),
            )
        )

    if cuisine_type:
        base_query = base_query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))

    if price_range and price_range in ["cheap", "mid", "expensive"]:
        base_query = base_query.filter(Restaurant.price_range == price_range)

    if min_rating is not None:
        base_query = base_query.filter(Restaurant.average_rating >= min_rating)

    return base_query.offset(skip).limit(limit).all()


def search_by_location(
    db: Session,
    latitude: Decimal,
    longitude: Decimal,
    radius_km: float = 5.0,
    skip: int = 0,
    limit: int = 100,
) -> list:
    lat_delta = Decimal(radius_km / 111)
    lon_delta = Decimal(radius_km / 111)

    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    return (
        db.query(Restaurant)
        .filter(
            Restaurant.status == "APPROVED",
            Restaurant.latitude.isnot(None),
            Restaurant.longitude.isnot(None),
            Restaurant.latitude >= min_lat,
            Restaurant.latitude <= max_lat,
            Restaurant.longitude >= min_lon,
            Restaurant.longitude <= max_lon,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_popular_restaurants(db: Session, limit: int = 10) -> list:
    return (
        db.query(Restaurant)
        .filter(Restaurant.status == "APPROVED")
        .order_by(Restaurant.average_rating.desc())
        .limit(limit)
        .all()
    )


def get_newly_added_restaurants(db: Session, limit: int = 10) -> list:
    return (
        db.query(Restaurant)
        .filter(Restaurant.status == "APPROVED")
        .order_by(Restaurant.created_at.desc())
        .limit(limit)
        .all()
    )
