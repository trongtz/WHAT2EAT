from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud.menu_item as crud_menu_item
import crud.restaurant as crud_restaurant
import crud.review as crud_review
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.dish import MenuItemResponse
from schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate
from schemas.review import ReviewResponse
from services.capacity_service import (
    attach_capacity_summary,
    get_restaurant_max_capacity,
    replace_restaurant_capacities,
)
from services.restaurant_service import attach_restaurant_review_summary

router = APIRouter()


@router.get("/search", response_model=list[RestaurantResponse])
def search_restaurants(
    query: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    min_rating: Optional[Decimal] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    restaurants = crud_restaurant.search_restaurants(
        db, query, cuisine_type, price_range, min_rating, skip, limit
    )
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/nearby", response_model=list[RestaurantResponse])
def get_nearby_restaurants(
    latitude: Decimal = Query(...),
    longitude: Decimal = Query(...),
    radius_km: float = Query(5.0),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    restaurants = crud_restaurant.search_by_location(db, latitude, longitude, radius_km, skip, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/popular", response_model=list[RestaurantResponse])
def get_popular_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    restaurants = crud_restaurant.get_popular_restaurants(db, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/new", response_model=list[RestaurantResponse])
def get_new_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    restaurants = crud_restaurant.get_newly_added_restaurants(db, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/", response_model=list[RestaurantResponse])
def get_all_restaurants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    restaurants = crud_restaurant.get_restaurants(db=db, skip=skip, limit=limit, status="APPROVED")
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/owner/{owner_id}", response_model=list[RestaurantResponse])
def get_owner_restaurants(
    owner_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.user_id != owner_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập",
        )
    restaurants = crud_restaurant.get_restaurants_by_owner(db, owner_id, skip, limit)
    for restaurant in restaurants:
        attach_capacity_summary(db, restaurant)
        attach_restaurant_review_summary(db, restaurant)
    return restaurants


@router.get("/manage/{restaurant_id}", response_model=RestaurantResponse)
def get_manage_restaurant_detail(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    if current_user.role != "ADMIN" and restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập nhà hàng này",
        )

    attach_capacity_summary(db, restaurant)
    attach_restaurant_review_summary(db, restaurant)
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_detail(restaurant_id: UUID, db: Session = Depends(get_db)):
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhà hàng không tồn tại hoặc chưa được duyệt",
        )
    attach_capacity_summary(db, restaurant)
    attach_restaurant_review_summary(db, restaurant)
    return restaurant


@router.get("/{restaurant_id}/menu", response_model=list[MenuItemResponse])
def get_restaurant_menu(
    restaurant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud_menu_item.get_menu_items_by_restaurant(db, restaurant_id, skip=skip, limit=limit)


@router.get("/{restaurant_id}/reviews", response_model=list[ReviewResponse])
def get_restaurant_reviews(
    restaurant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud_review.get_reviews_by_restaurant(db, restaurant_id, skip=skip, limit=limit)


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhà hàng mới được quyền tạo nhà hàng",
        )

    created_restaurant = crud_restaurant.create_restaurant(
        db=db,
        restaurant=restaurant,
        owner_id=current_user.user_id,
    )
    replace_restaurant_capacities(
        db,
        created_restaurant.restaurant_id,
        restaurant.open_hours,
        restaurant.max_capacity,
    )
    db.refresh(created_restaurant)
    attach_capacity_summary(db, created_restaurant)
    attach_restaurant_review_summary(db, created_restaurant)
    return created_restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: UUID,
    restaurant_in: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    if db_restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật nhà hàng này",
        )

    if db_restaurant.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nhà hàng chỉ được chỉnh sửa sau khi admin đã duyệt",
        )

    max_capacity = restaurant_in.max_capacity
    updated_restaurant = crud_restaurant.update_restaurant(db, restaurant_id, restaurant_in)
    if not updated_restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    if max_capacity is not None or restaurant_in.open_hours is not None:
        replace_restaurant_capacities(
            db,
            updated_restaurant.restaurant_id,
            updated_restaurant.open_hours,
            max_capacity if max_capacity is not None else get_restaurant_max_capacity(db, updated_restaurant.restaurant_id),
        )
        db.refresh(updated_restaurant)

    attach_capacity_summary(db, updated_restaurant)
    attach_restaurant_review_summary(db, updated_restaurant)
    return updated_restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhà hàng không tồn tại")

    if db_restaurant.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa nhà hàng này",
        )

    crud_restaurant.delete_restaurant(db, restaurant_id)
    return None
