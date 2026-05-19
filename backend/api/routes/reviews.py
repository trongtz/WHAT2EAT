from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import crud.reservation as crud_reservation
import crud.restaurant as crud_restaurant
import crud.review as crud_review
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()


class ReviewCreateRequest(BaseModel):
    restaurant_id: UUID = Field(validation_alias="restaurantId")
    reservation_id: UUID | None = Field(default=None, validation_alias="reservationId")
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None

    model_config = {"populate_by_name": True}


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can create reviews")

    restaurant = crud_restaurant.get_restaurant_by_id(db, payload.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    if payload.reservation_id:
        reservation = crud_reservation.get_reservation_by_id(db, payload.reservation_id)
        if (
            not reservation
            or reservation.customer_id != current_user.user_id
            or reservation.restaurant_id != payload.restaurant_id
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reservation for review")
        if crud_review.get_review_by_reservation(db, payload.reservation_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reservation already has a review")

    review_in = ReviewCreate(
        rating=payload.rating,
        comment=payload.comment,
        reservation_id=payload.reservation_id,
    )
    return crud_review.create_review(db, review_in, current_user.user_id, payload.restaurant_id)
