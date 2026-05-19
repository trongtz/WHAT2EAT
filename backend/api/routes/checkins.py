from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.checkin as crud_checkin
import crud.restaurant as crud_restaurant
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.checkin import CheckInCreate, CheckInResponse

router = APIRouter()


@router.post("/", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def create_checkin(
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chi khach hang moi co the check-in")

    restaurant = crud_restaurant.get_restaurant_by_id(db, payload.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay nha hang")

    return crud_checkin.create_checkin(db, payload, current_user.user_id)


@router.get("/me", response_model=list[CheckInResponse])
def get_my_checkins(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chi khach hang moi co lich su check-in")
    return crud_checkin.get_checkins_by_customer(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/restaurants/{restaurant_id}", response_model=list[CheckInResponse])
def get_restaurant_checkins(
    restaurant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud_checkin.get_checkins_by_restaurant(db, restaurant_id, skip=skip, limit=limit)
