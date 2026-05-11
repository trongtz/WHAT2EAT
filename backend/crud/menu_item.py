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


def get_menu_items_by_restaurant(
    db: Session,
    restaurant_id: UUID,
    category: str = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> list:
    """Lấy danh sách menu items của nhà hàng"""
    query = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)
    
    # Filter by category
    if category:
        query = query.filter(MenuItem.category == category)
    
    # Filter available items only
    if available_only:
        query = query.filter(MenuItem.is_available == True)
    
    return query.offset(skip).limit(limit).all()


def get_available_items_by_restaurant(
    db: Session,
    restaurant_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> list:
    """Lấy danh sách menu items còn hàng của nhà hàng"""
    return db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
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


def toggle_menu_item_availability(db: Session, item_id: UUID) -> MenuItem | None:
    """Chuyển đổi trạng thái còn hàng/hết hàng của menu item"""
    db_item = get_menu_item_by_id(db, item_id)
    if not db_item:
        return None
    
    db_item.is_available = not db_item.is_available
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


def get_categories_by_restaurant(db: Session, restaurant_id: UUID) -> list:
    """Lấy danh sách loại món của nhà hàng"""
    categories = db.query(MenuItem.category).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.category.isnot(None)
    ).distinct().all()
    return [cat[0] for cat in categories]

