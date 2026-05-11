from uuid import UUID
from sqlalchemy.orm import Session
from models.dish import MenuItem
from schemas.dish import MenuItemCreate, MenuItemUpdate


def create_menu_item(db: Session, item_in: MenuItemCreate, restaurant_id: UUID) -> MenuItem:
    """Tạo menu item mới"""
    db_item = MenuItem(
        **item_in.model_dump(exclude_unset=True),
        restaurant_id=restaurant_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_menu_item_by_id(db: Session, item_id: UUID) -> MenuItem | None:
    """Lấy menu item theo ID"""
    return db.query(MenuItem).filter(MenuItem.item_id == item_id).first()


def get_menu_items_by_restaurant(db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách menu items của nhà hàng"""
    return db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id
    ).offset(skip).limit(limit).all()


def update_menu_item(db: Session, item_id: UUID, item_in: MenuItemUpdate) -> MenuItem | None:
    """Cập nhật menu item"""
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return None
    
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db: Session, item_id: UUID) -> bool:
    """Xóa menu item"""
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return False
    
    db.delete(db_item)
    db.commit()
    return True
