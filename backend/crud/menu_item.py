from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.dish import MenuItem
from schemas.dish import MenuItemCreate, MenuItemUpdate


def _menu_item_data(schema: MenuItemCreate | MenuItemUpdate) -> dict:
    data = schema.model_dump(exclude_unset=True, exclude_none=True)
    data.pop("is_available", None)
    return data


def create_menu_item(db: Session, item_in: MenuItemCreate, restaurant_id: UUID) -> MenuItem:
    db_item = MenuItem(
        **_menu_item_data(item_in),
        restaurant_id=restaurant_id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_menu_item_by_id(db: Session, item_id: UUID) -> MenuItem | None:
    return db.query(MenuItem).filter(MenuItem.item_id == item_id).first()


def get_menu_items_by_restaurant(
    db: Session,
    restaurant_id: UUID,
    category: str | None = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[MenuItem]:
    query = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)
    if category:
        query = query.filter(MenuItem.category == category)
    if available_only:
        query = query.filter(MenuItem.availability_status == "AVAILABLE")
    return query.offset(skip).limit(limit).all()


def get_available_items_by_restaurant(
    db: Session,
    restaurant_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[MenuItem]:
    return (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.availability_status == "AVAILABLE",
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_menu_item(db: Session, item_id: UUID, item_in: MenuItemUpdate) -> MenuItem | None:
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return None

    for field, value in _menu_item_data(item_in).items():
        setattr(db_item, field, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def toggle_menu_item_availability(db: Session, item_id: UUID) -> MenuItem | None:
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return None

    db_item.is_available = not db_item.is_available
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db: Session, item_id: UUID) -> bool:
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True


def get_categories_by_restaurant(db: Session, restaurant_id: UUID) -> list[str]:
    categories = (
        db.query(MenuItem.category)
        .filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.category.isnot(None),
        )
        .distinct()
        .all()
    )
    return [category[0] for category in categories]
