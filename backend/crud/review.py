from uuid import UUID

from sqlalchemy.orm import Session

from models.review import Review
from schemas.review import ReviewCreate


def create_review(db: Session, review_in: ReviewCreate, customer_id: UUID, restaurant_id: UUID) -> Review:
    db_review = Review(
        **review_in.model_dump(exclude_unset=True),
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        status="PENDING",
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def get_review_by_id(db: Session, review_id: UUID) -> Review | None:
    return db.query(Review).filter(Review.review_id == review_id).first()


def get_reviews_by_restaurant(db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100) -> list:
    return (
        db.query(Review)
        .filter(
            Review.restaurant_id == restaurant_id,
            Review.status != "REJECTED",
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_reviews_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 100) -> list:
    return db.query(Review).filter(Review.customer_id == customer_id).offset(skip).limit(limit).all()


def get_review_by_reservation(db: Session, reservation_id: UUID) -> Review | None:
    return db.query(Review).filter(Review.reservation_id == reservation_id).first()


def approve_review(db: Session, review_id: UUID) -> Review | None:
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None

    db_review.status = "APPROVED"
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def reject_review(db: Session, review_id: UUID, rejection_reason: str) -> Review | None:
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None

    db_review.status = "REJECTED"
    db_review.rejection_reason = rejection_reason
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
