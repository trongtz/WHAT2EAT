from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.review import Review
from schemas.review import ReviewCreate


def serialize_review(review: Review) -> dict:
    return {
        "id": review.review_id,
        "review_id": review.review_id,
        "customer_id": review.customer_id,
        "restaurant_id": review.restaurant_id,
        "reservation_id": review.reservation_id,
        "rating": review.rating,
        "comment": review.comment,
        "status": review.status,
        "rejection_reason": review.rejection_reason,
        "user_name": review.customer.full_name if review.customer else "Khách hàng",
        "userName": review.customer.full_name if review.customer else "Khách hàng",
        "created_at": review.created_at,
        "updated_at": review.updated_at,
    }


def create_review(db: Session, review_in: ReviewCreate, customer_id: UUID, restaurant_id: UUID) -> Review:
    """Tạo review mới"""
    db_review = Review(
        **review_in.model_dump(exclude_unset=True),
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        status="APPROVED",
    )
    db.add(db_review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_review)
    return db_review


def get_review_by_id(db: Session, review_id: UUID) -> Review | None:
    """Lấy review theo ID"""
    return db.query(Review).filter(Review.review_id == review_id).first()


def get_review_by_customer_and_restaurant(
    db: Session,
    customer_id: UUID,
    restaurant_id: UUID,
) -> Review | None:
    return (
        db.query(Review)
        .filter(Review.customer_id == customer_id, Review.restaurant_id == restaurant_id)
        .first()
    )


def get_reviews_by_restaurant(db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách reviews của nhà hàng (APPROVED only)"""
    return (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id, Review.status == "APPROVED")
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_reviews_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 100) -> list:
    """Lấy danh sách reviews của khách hàng"""
    return (
        db.query(Review)
        .filter(Review.customer_id == customer_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_review_by_reservation(db: Session, reservation_id: UUID) -> Review | None:
    """Lấy review theo reservation_id"""
    return db.query(Review).filter(Review.reservation_id == reservation_id).first()


def approve_review(db: Session, review_id: UUID) -> Review | None:
    """Admin duyệt review"""
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None

    db_review.status = "APPROVED"
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def reject_review(db: Session, review_id: UUID, rejection_reason: str) -> Review | None:
    """Admin từ chối review"""
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None

    db_review.status = "REJECTED"
    db_review.rejection_reason = rejection_reason
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
