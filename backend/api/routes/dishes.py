from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.menu_item as crud_menu_item
from api.deps import get_current_user
from core.database import get_db
from models.restaurant import Restaurant
from models.user import User
from schemas.dish import DishCreate, DishResponse, DishUpdate

router = APIRouter()


def validate_owner_restaurant_access(restaurant: Restaurant | None, current_user: User) -> None:
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà hàng này")

    if restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền thao tác với nhà hàng của người khác",
        )

    if restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=403,
            detail="Chỉ được cập nhật menu sau khi nhà hàng đã được admin duyệt",
        )


@router.post("/restaurant/{restaurant_id}", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    restaurant_id: UUID,
    dish_in: DishCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    validate_owner_restaurant_access(restaurant, current_user)
    return crud_menu_item.create_menu_item(db, dish_in, restaurant_id)


@router.put("/{item_id}", response_model=DishResponse)
def update_dish(
    item_id: UUID,
    dish_in: DishUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_dish = crud_menu_item.get_menu_item_by_id(db, item_id)
    if not db_dish:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn")

    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == db_dish.restaurant_id).first()
    validate_owner_restaurant_access(restaurant, current_user)

    updated_dish = crud_menu_item.update_menu_item(db, item_id, dish_in)
    if not updated_dish:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn")
    return updated_dish


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_dish = crud_menu_item.get_menu_item_by_id(db, item_id)
    if not db_dish:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn")

    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == db_dish.restaurant_id).first()
    validate_owner_restaurant_access(restaurant, current_user)
    crud_menu_item.delete_menu_item(db, item_id)
    return None


@router.get("/restaurant/{restaurant_id}", response_model=List[DishResponse])
def get_dishes_by_restaurant(restaurant_id: UUID, db: Session = Depends(get_db)):
    return crud_menu_item.get_menu_items_by_restaurant(db, restaurant_id)
