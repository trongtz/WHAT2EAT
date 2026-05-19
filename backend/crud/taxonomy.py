from uuid import UUID

from sqlalchemy.orm import Session

from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine, RestaurantImage
from schemas.taxonomy import CuisineCategoryCreate, RestaurantImageCreate


def create_cuisine_category(db: Session, payload: CuisineCategoryCreate) -> CuisineCategory:
    category = CuisineCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_cuisine_categories(db: Session) -> list[CuisineCategory]:
    return db.query(CuisineCategory).order_by(CuisineCategory.name.asc()).all()


def link_restaurant_cuisine(db: Session, restaurant_id: UUID, category_id: UUID) -> RestaurantCuisine:
    existing = (
        db.query(RestaurantCuisine)
        .filter(RestaurantCuisine.restaurant_id == restaurant_id, RestaurantCuisine.category_id == category_id)
        .first()
    )
    if existing:
        return existing

    link = RestaurantCuisine(restaurant_id=restaurant_id, category_id=category_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def create_restaurant_image(db: Session, restaurant_id: UUID, payload: RestaurantImageCreate) -> RestaurantImage:
    image = RestaurantImage(restaurant_id=restaurant_id, **payload.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_restaurant_images(db: Session, restaurant_id: UUID) -> list[RestaurantImage]:
    return (
        db.query(RestaurantImage)
        .filter(RestaurantImage.restaurant_id == restaurant_id)
        .order_by(RestaurantImage.uploaded_at.desc())
        .all()
    )
