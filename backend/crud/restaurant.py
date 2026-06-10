from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from models.restaurant import Restaurant
from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine, RestaurantImage
from schemas.restaurant import RestaurantCreate, RestaurantUpdate
from services.opening_hours_service import normalize_opening_hours


def _extract_related_restaurant_data(data: dict) -> tuple[list[str] | None, str | None, list[UUID] | None]:
    images = data.pop("images", None)
    cuisine_type = data.pop("cuisine_type", None)
    cuisine_category_ids = data.pop("cuisine_category_ids", None)
    legacy_open_hours = data.pop("open_hours", None)
    if "opening_hours" not in data and legacy_open_hours is not None:
        data["opening_hours"] = legacy_open_hours
    if "opening_hours" in data:
        data["opening_hours"] = normalize_opening_hours(data["opening_hours"])
    data.pop("max_capacity", None)
    return images, cuisine_type, cuisine_category_ids


def _replace_restaurant_images(db: Session, restaurant_id: UUID, image_urls: list[str] | None) -> None:
    if image_urls is None:
        return

    db.query(RestaurantImage).filter(RestaurantImage.restaurant_id == restaurant_id).delete()
    for index, image_url in enumerate(image_urls):
        if not image_url:
            continue
        db.add(
            RestaurantImage(
                restaurant_id=restaurant_id,
                image_url=image_url,
                image_type="cover" if index == 0 else "general",
            )
        )


def _replace_restaurant_cuisines(
    db: Session,
    restaurant_id: UUID,
    cuisine_type: str | None,
    cuisine_category_ids: list[UUID] | None,
) -> None:
    if cuisine_type is None and cuisine_category_ids is None:
        return

    db.query(RestaurantCuisine).filter(RestaurantCuisine.restaurant_id == restaurant_id).delete()
    category_ids = list(cuisine_category_ids or [])

    if cuisine_type:
        for cuisine_name in [item.strip() for item in cuisine_type.split(",") if item.strip()]:
            category = db.query(CuisineCategory).filter(CuisineCategory.name.ilike(cuisine_name)).first()
            if not category:
                category = CuisineCategory(name=cuisine_name)
                db.add(category)
                db.flush()
            category_ids.append(category.category_id)

    for category_id in dict.fromkeys(category_ids):
        db.add(RestaurantCuisine(restaurant_id=restaurant_id, category_id=category_id))


def create_restaurant(db: Session, restaurant: RestaurantCreate, owner_id: UUID) -> Restaurant:
    restaurant_data = restaurant.model_dump(exclude_unset=True)
    images, cuisine_type, cuisine_category_ids = _extract_related_restaurant_data(restaurant_data)
    db_restaurant = Restaurant(
        **restaurant_data,
        owner_id=owner_id,
        approval_status="PENDING",
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)

    _replace_restaurant_images(db, db_restaurant.restaurant_id, images or [])
    _replace_restaurant_cuisines(db, db_restaurant.restaurant_id, cuisine_type, cuisine_category_ids)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def get_restaurants(db: Session, skip: int = 0, limit: int = 100, status: str | None = None) -> list:
    query = db.query(Restaurant).options(
        selectinload(Restaurant.restaurant_images),
        selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
    )
    if status:
        query = query.filter(Restaurant.approval_status == status)
    else:
        query = query.filter(Restaurant.approval_status == "APPROVED", Restaurant.is_active.is_(True))
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
    images, cuisine_type, cuisine_category_ids = _extract_related_restaurant_data(update_data)
    for field, value in update_data.items():
        setattr(db_restaurant, field, value)

    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)

    _replace_restaurant_images(db, restaurant_id, images)
    _replace_restaurant_cuisines(db, restaurant_id, cuisine_type, cuisine_category_ids)
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
    base_query = db.query(Restaurant).options(
        selectinload(Restaurant.restaurant_images),
        selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
    ).filter(
        Restaurant.approval_status == "APPROVED",
        Restaurant.is_active.is_(True),
    )

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Restaurant.name.ilike(search_term),
                Restaurant.address.ilike(search_term),
                Restaurant.description.ilike(search_term),
            )
        )

    if cuisine_type:
        base_query = (
            base_query.join(RestaurantCuisine, RestaurantCuisine.restaurant_id == Restaurant.restaurant_id)
            .join(CuisineCategory, CuisineCategory.category_id == RestaurantCuisine.category_id)
            .filter(CuisineCategory.name.ilike(f"%{cuisine_type}%"))
        )

    if price_range:
        base_query = base_query.filter(Restaurant.price_range == price_range)

    if min_rating is not None:
        base_query = base_query.filter(Restaurant.rating_avg >= min_rating)

    return base_query.distinct().offset(skip).limit(limit).all()


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
        .options(
            selectinload(Restaurant.restaurant_images),
            selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
        )
        .filter(
            Restaurant.approval_status == "APPROVED",
            Restaurant.is_active.is_(True),
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
        .options(
            selectinload(Restaurant.restaurant_images),
            selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
        )
        .filter(Restaurant.approval_status == "APPROVED", Restaurant.is_active.is_(True))
        .order_by(Restaurant.rating_avg.desc())
        .limit(limit)
        .all()
    )


def get_newly_added_restaurants(db: Session, limit: int = 10) -> list:
    return (
        db.query(Restaurant)
        .options(
            selectinload(Restaurant.restaurant_images),
            selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
        )
        .filter(Restaurant.approval_status == "APPROVED", Restaurant.is_active.is_(True))
        .order_by(Restaurant.created_at.desc())
        .limit(limit)
        .all()
    )
