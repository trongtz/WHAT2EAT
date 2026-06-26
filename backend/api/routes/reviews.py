from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
import crud.review as crud_review
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate

router = APIRouter()


class ReviewCreateRequest(BaseModel):
    restaurant_id: UUID = Field(validation_alias="restaurantId")
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None

    model_config = {"populate_by_name": True}


def _require_customer(current_user: User) -> None:
    if (current_user.role or "").upper() != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ khách hàng mới được đánh giá nhà hàng",
        )


@router.get("/me", response_model=list[ReviewResponse])
def get_my_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer(current_user)
    reviews = crud_review.get_reviews_by_customer(db, current_user.user_id, skip=skip, limit=limit)
    return [crud_review.serialize_review(review) for review in reviews]


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer(current_user)

    restaurant = crud_restaurant.get_restaurant_by_id(db, payload.restaurant_id)
    if not restaurant or restaurant.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhà hàng")

    existing_review = crud_review.get_review_by_customer_and_restaurant(
        db,
        current_user.user_id,
        payload.restaurant_id,
    )
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn chỉ được đánh giá mỗi nhà hàng một lần",
        )

    review_in = ReviewCreate(rating=payload.rating, comment=payload.comment)
    try:
        review = crud_review.create_review(db, review_in, current_user.user_id, payload.restaurant_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn chỉ được đánh giá mỗi nhà hàng một lần",
        ) from None

    return crud_review.serialize_review(review)


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: UUID,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer(current_user)

    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đánh giá")

    if review.customer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền sửa đánh giá này")

    if payload.rating is None and payload.comment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không có thông tin cần cập nhật")

    updated_review = crud_review.update_review(db, review, payload)
    return crud_review.serialize_review(updated_review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer(current_user)

    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đánh giá")

    if review.customer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xoá đánh giá này")

    crud_review.delete_review(db, review)
