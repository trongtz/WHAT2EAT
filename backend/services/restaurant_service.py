from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.booking import Reservation
from models.restaurant import Restaurant
from models.review import Review


def calculate_average_rating(db: Session, restaurant_id: UUID) -> Decimal:
    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(
            Review.restaurant_id == restaurant_id,
            Review.status != "REJECTED",
        )
        .scalar()
    )

    if avg_rating is None:
        return Decimal("0.00")

    return Decimal(str(avg_rating)).quantize(Decimal("0.01"))


def get_restaurant_review_stats(db: Session, restaurant_id: UUID) -> dict:
    average_rating, total_reviews = (
        db.query(func.avg(Review.rating), func.count(Review.review_id))
        .filter(
            Review.restaurant_id == restaurant_id,
            Review.status != "REJECTED",
        )
        .first()
    )

    if average_rating is None:
        return {
            "average_rating": Decimal("0.00"),
            "total_reviews": 0,
        }

    return {
        "average_rating": Decimal(str(average_rating)).quantize(Decimal("0.01")),
        "total_reviews": int(total_reviews or 0),
    }


def attach_restaurant_review_summary(db: Session, restaurant: Restaurant) -> Restaurant:
    stats = get_restaurant_review_stats(db, restaurant.restaurant_id)
    if stats["total_reviews"] > 0:
        restaurant.average_rating = stats["average_rating"]
    elif restaurant.average_rating is None:
        restaurant.average_rating = Decimal("0.00")
    setattr(restaurant, "review_count", stats["total_reviews"])
    return restaurant


def attach_restaurant_review_summaries(db: Session, restaurants: list[Restaurant]) -> list[Restaurant]:
    if not restaurants:
        return restaurants

    restaurant_ids = [restaurant.restaurant_id for restaurant in restaurants]
    stats_by_restaurant = {
        restaurant_id: {
            "average_rating": Decimal(str(average_rating)).quantize(Decimal("0.01"))
            if average_rating is not None
            else Decimal("0.00"),
            "total_reviews": int(total_reviews or 0),
        }
        for restaurant_id, average_rating, total_reviews in (
            db.query(Review.restaurant_id, func.avg(Review.rating), func.count(Review.review_id))
            .filter(
                Review.restaurant_id.in_(restaurant_ids),
                Review.status != "REJECTED",
            )
            .group_by(Review.restaurant_id)
            .all()
        )
    }

    for restaurant in restaurants:
        stats = stats_by_restaurant.get(
            restaurant.restaurant_id,
            {"average_rating": Decimal("0.00"), "total_reviews": 0},
        )
        if stats["total_reviews"] > 0:
            restaurant.average_rating = stats["average_rating"]
        elif restaurant.average_rating is None:
            restaurant.average_rating = Decimal("0.00")
        setattr(restaurant, "review_count", stats["total_reviews"])

    return restaurants


def update_restaurant_rating(db: Session, restaurant_id: UUID) -> Restaurant | None:
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return None

    new_rating = calculate_average_rating(db, restaurant_id)
    restaurant.average_rating = new_rating
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def get_restaurant_stats(db: Session, restaurant_id: UUID) -> dict:
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return {}

    review_stats = get_restaurant_review_stats(db, restaurant_id)

    total_reservations = (
        db.query(Reservation)
        .filter(Reservation.restaurant_id == restaurant_id)
        .count()
    )

    confirmed_reservations = (
        db.query(Reservation)
        .filter(
            Reservation.restaurant_id == restaurant_id,
            Reservation.status == "CONFIRMED",
        )
        .count()
    )

    from models.dish import MenuItem

    total_menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == restaurant_id)
        .count()
    )

    available_menu_items = (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.availability_status == "AVAILABLE",
        )
        .count()
    )

    return {
        "restaurant_id": str(restaurant_id),
        "average_rating": float(review_stats["average_rating"]),
        "total_reviews": review_stats["total_reviews"],
        "total_reservations": total_reservations,
        "confirmed_reservations": confirmed_reservations,
        "total_menu_items": total_menu_items,
        "available_menu_items": available_menu_items,
    }
