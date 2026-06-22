from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.booking import Reservation
from models.checkin import CheckIn
from models.favorite import Favorite
from models.restaurant import Restaurant
from models.review import Review


@dataclass
class RestaurantSignals:
    rating_avg: float
    rating_count: int
    checkin_count_30d: int
    favorite_count: int
    booking_count_30d: int
    quality_score: float
    quality_reasons: list[str]


def get_restaurant_signals(db: Session, restaurant: Restaurant) -> RestaurantSignals:
    restaurant_id = restaurant.restaurant_id
    since = datetime.utcnow() - timedelta(days=30)

    rating_avg = float(getattr(restaurant, "rating_avg", None) or getattr(restaurant, "average_rating", None) or 0)
    rating_count = _count(db, Review, Review.restaurant_id == restaurant_id, Review.status == "APPROVED")
    if rating_avg <= 0 and rating_count > 0:
        rating_avg = float(
            db.query(func.avg(Review.rating))
            .filter(Review.restaurant_id == restaurant_id, Review.status == "APPROVED")
            .scalar()
            or 0
        )

    checkin_count = _count(db, CheckIn, CheckIn.restaurant_id == restaurant_id, CheckIn.checkin_at >= since)
    favorite_count = _count(db, Favorite, Favorite.restaurant_id == restaurant_id)
    booking_count = _count(db, Reservation, Reservation.restaurant_id == restaurant_id, Reservation.created_at >= since)
    quality_score = _quality_score(rating_avg, rating_count, checkin_count, favorite_count, booking_count)
    reasons = _quality_reasons(rating_avg, rating_count, checkin_count, favorite_count, booking_count)

    return RestaurantSignals(
        rating_avg=round(rating_avg, 2),
        rating_count=rating_count,
        checkin_count_30d=checkin_count,
        favorite_count=favorite_count,
        booking_count_30d=booking_count,
        quality_score=round(quality_score, 4),
        quality_reasons=reasons,
    )


def get_restaurant_signals_map(db: Session, restaurants: list[Restaurant]) -> dict[Any, RestaurantSignals]:
    if not restaurants:
        return {}

    restaurant_ids = [restaurant.restaurant_id for restaurant in restaurants]
    since = datetime.utcnow() - timedelta(days=30)

    review_rows = db.query(
        Review.restaurant_id,
        func.count().label("rating_count"),
        func.avg(Review.rating).label("rating_avg"),
    ).filter(
        Review.restaurant_id.in_(restaurant_ids),
        Review.status == "APPROVED",
    ).group_by(Review.restaurant_id).all()
    review_map = {
        restaurant_id: {
            "rating_count": int(rating_count or 0),
            "rating_avg": float(rating_avg or 0),
        }
        for restaurant_id, rating_count, rating_avg in review_rows
    }

    checkin_map = dict(
        db.query(CheckIn.restaurant_id, func.count())
        .filter(CheckIn.restaurant_id.in_(restaurant_ids), CheckIn.checkin_at >= since)
        .group_by(CheckIn.restaurant_id)
        .all()
    )
    favorite_map = dict(
        db.query(Favorite.restaurant_id, func.count())
        .filter(Favorite.restaurant_id.in_(restaurant_ids))
        .group_by(Favorite.restaurant_id)
        .all()
    )
    booking_map = dict(
        db.query(Reservation.restaurant_id, func.count())
        .filter(Reservation.restaurant_id.in_(restaurant_ids), Reservation.created_at >= since)
        .group_by(Reservation.restaurant_id)
        .all()
    )

    signals_by_restaurant: dict[Any, RestaurantSignals] = {}
    for restaurant in restaurants:
        restaurant_id = restaurant.restaurant_id
        review_info = review_map.get(restaurant_id, {})
        rating_avg = float(getattr(restaurant, "rating_avg", None) or getattr(restaurant, "average_rating", None) or review_info.get("rating_avg") or 0)
        rating_count = int(review_info.get("rating_count") or 0)
        checkin_count = int(checkin_map.get(restaurant_id) or 0)
        favorite_count = int(favorite_map.get(restaurant_id) or 0)
        booking_count = int(booking_map.get(restaurant_id) or 0)
        quality_score = _quality_score(rating_avg, rating_count, checkin_count, favorite_count, booking_count)
        signals_by_restaurant[restaurant_id] = RestaurantSignals(
            rating_avg=round(rating_avg, 2),
            rating_count=rating_count,
            checkin_count_30d=checkin_count,
            favorite_count=favorite_count,
            booking_count_30d=booking_count,
            quality_score=round(quality_score, 4),
            quality_reasons=_quality_reasons(rating_avg, rating_count, checkin_count, favorite_count, booking_count),
        )
    return signals_by_restaurant


def availability_score(available_capacity: int | None, group_size: int | None) -> tuple[float, list[str]]:
    if available_capacity is None:
        return 0.0, []
    if available_capacity <= 0:
        return -0.6, ["Hiện có thể đã hết chỗ"]
    if group_size is not None and available_capacity < group_size:
        return -0.45, [f"Có thể không đủ chỗ cho nhóm {group_size} người"]

    score = min(available_capacity / 40.0, 1.0)
    reasons: list[str] = []
    if group_size is not None:
        reasons.append(f"Còn đủ sức chứa cho nhóm {group_size} người")
    elif available_capacity >= 20:
        reasons.append("Hiện còn nhiều chỗ")
    else:
        reasons.append("Hiện còn chỗ")
    return score, reasons


def _count(db: Session, model: Any, *filters: Any) -> int:
    try:
        return int(db.query(func.count()).select_from(model).filter(*filters).scalar() or 0)
    except Exception:
        return 0


def _quality_score(
    rating_avg: float,
    rating_count: int,
    checkin_count: int,
    favorite_count: int,
    booking_count: int,
) -> float:
    rating_component = max(min((rating_avg - 2.5) / 2.5, 1.0), 0.0)
    return min(
        1.0,
        0.40 * rating_component
        + 0.20 * _normalized_log(rating_count, 300)
        + 0.18 * _normalized_log(checkin_count, 500)
        + 0.12 * _normalized_log(favorite_count, 250)
        + 0.10 * _normalized_log(booking_count, 160),
    )


def _quality_reasons(
    rating_avg: float,
    rating_count: int,
    checkin_count: int,
    favorite_count: int,
    booking_count: int,
) -> list[str]:
    reasons: list[str] = []
    if rating_avg >= 4.3 and rating_count >= 10:
        reasons.append(f"Được đánh giá tốt ({rating_avg:.1f}/5)")
    elif rating_avg >= 4.0:
        reasons.append(f"Rating ổn ({rating_avg:.1f}/5)")
    if checkin_count >= 20:
        reasons.append(f"Nhiều check-in gần đây ({checkin_count}/30 ngày)")
    if favorite_count >= 20:
        reasons.append(f"Nhiều lượt yêu thích ({favorite_count})")
    if booking_count >= 10:
        reasons.append(f"Có nhiều lượt đặt bàn gần đây ({booking_count}/30 ngày)")
    return reasons[:3]


def _normalized_log(value: int, max_value: int) -> float:
    return min(math.log1p(max(value, 0)) / math.log1p(max_value), 1.0)
