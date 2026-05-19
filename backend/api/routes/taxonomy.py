from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
import crud.taxonomy as crud_taxonomy
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.taxonomy import (
    CuisineCategoryCreate,
    CuisineCategoryResponse,
    RestaurantCuisineLink,
    RestaurantImageCreate,
    RestaurantImageResponse,
)

router = APIRouter()


def require_admin(current_user: User) -> None:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chi admin moi co quyen quan ly danh muc")


def require_restaurant_owner_or_admin(db: Session, restaurant_id: UUID, current_user: User):
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay nha hang")
    if current_user.role != "ADMIN" and restaurant.owner_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong co quyen quan ly nha hang nay")
    return restaurant


@router.get("/cuisines", response_model=list[CuisineCategoryResponse])
def get_cuisine_categories(db: Session = Depends(get_db)):
    return crud_taxonomy.get_cuisine_categories(db)


@router.post("/cuisines", response_model=CuisineCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_cuisine_category(
    payload: CuisineCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    return crud_taxonomy.create_cuisine_category(db, payload)


@router.post("/restaurants/{restaurant_id}/cuisines", status_code=status.HTTP_204_NO_CONTENT)
def link_restaurant_cuisine(
    restaurant_id: UUID,
    payload: RestaurantCuisineLink,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_restaurant_owner_or_admin(db, restaurant_id, current_user)
    crud_taxonomy.link_restaurant_cuisine(db, restaurant_id, payload.category_id)
    return None


@router.get("/restaurants/{restaurant_id}/images", response_model=list[RestaurantImageResponse])
def get_restaurant_images(restaurant_id: UUID, db: Session = Depends(get_db)):
    return crud_taxonomy.get_restaurant_images(db, restaurant_id)


@router.post(
    "/restaurants/{restaurant_id}/images",
    response_model=RestaurantImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant_image(
    restaurant_id: UUID,
    payload: RestaurantImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_restaurant_owner_or_admin(db, restaurant_id, current_user)
    return crud_taxonomy.create_restaurant_image(db, restaurant_id, payload)
