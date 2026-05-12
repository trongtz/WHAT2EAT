from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.menu_item as crud_menu_item
import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.dish import MenuItemCreate, MenuItemResponse, MenuItemUpdate

router = APIRouter()


@router.get("/restaurant/{restaurant_id}", response_model=list[MenuItemResponse])
def get_dishes_by_restaurant(restaurant_id: UUID, db: Session = Depends(get_db)):
    return crud_menu_item.get_menu_items_by_restaurant(db, restaurant_id)


@router.post("/restaurant/{restaurant_id}", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    restaurant_id: UUID,
    dish_in: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng")

    if restaurant.owner_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thêm món")

    if restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nhà hàng chỉ được cập nhật menu sau khi admin đã duyệt",
        )

    return crud_menu_item.create_menu_item(db, dish_in, restaurant_id)


@router.put("/{item_id}", response_model=MenuItemResponse)
def update_dish(
    item_id: UUID,
    item_in: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    menu_item = crud_menu_item.get_menu_item_by_id(db, item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy món ăn")

    restaurant = crud_restaurant.get_restaurant_by_id(db, menu_item.restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền cập nhật món ăn")

    if restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nhà hàng chỉ được cập nhật menu sau khi admin đã duyệt",
        )

    updated_item = crud_menu_item.update_menu_item(db, item_id, item_in)
    if not updated_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy món ăn")
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    menu_item = crud_menu_item.get_menu_item_by_id(db, item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy món ăn")

    restaurant = crud_restaurant.get_restaurant_by_id(db, menu_item.restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xóa món ăn")

    if restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nhà hàng chỉ được cập nhật menu sau khi admin đã duyệt",
        )

    crud_menu_item.delete_menu_item(db, item_id)
    return None
