from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.booking import Reservation
from models.checkin import CheckIn
from models.customer_profile import CustomerProfile
from models.favorite import Favorite
from models.restaurant import Restaurant
from models.review import Review
from models.search_history import SearchHistory
from models.user import User
from services.ai_assistant.recommend_imports import normalize_text, tokenize


def get_user_preference_tool(db: Session, current_user: User | None) -> dict[str, Any]:
    if not current_user:
        return {"enabled": False}

    customer_id = current_user.user_id
    customer_profile = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer_id).first()
    enabled = bool(customer_profile.personalization_enabled) if customer_profile else True
    if not enabled:
        return {"enabled": False}

    recent_histories = (
        db.query(SearchHistory)
        .filter(SearchHistory.customer_id == customer_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "enabled": True,
        "favorite_ids": _restaurant_ids(db.query(Favorite.restaurant_id).filter(Favorite.customer_id == customer_id).all()),
        "checked_in_ids": _restaurant_ids(
            db.query(CheckIn.restaurant_id)
            .filter(CheckIn.customer_id == customer_id, CheckIn.is_verified.is_(True))
            .all()
        ),
        "reserved_ids": _restaurant_ids(
            db.query(Reservation.restaurant_id)
            .filter(Reservation.customer_id == customer_id, Reservation.status.in_(["CONFIRMED", "COMPLETED"]))
            .all()
        ),
        "reviewed_ids": _restaurant_ids(
            db.query(Review.restaurant_id)
            .filter(Review.customer_id == customer_id, Review.status == "APPROVED", Review.rating >= 4)
            .all()
        ),
        "recent_tokens": set(token for history in recent_histories for token in tokenize(history.query_text or "")),
        "preferred_cuisines": set(map(normalize_text, customer_profile.preferred_cuisines or [])) if customer_profile else set(),
        "preferred_locations": set(map(normalize_text, customer_profile.preferred_locations or [])) if customer_profile else set(),
        "preferred_price_range": customer_profile.preferred_price_range if customer_profile else None,
    }


def user_behavior_score(restaurant: Restaurant, user_profile: dict[str, Any], search_text: str) -> tuple[float, str]:
    if not user_profile.get("enabled"):
        return 0.0, ""

    restaurant_id = str(restaurant.restaurant_id)
    score = 0.0
    reasons: list[str] = []

    if restaurant_id in user_profile.get("favorite_ids", set()):
        score += 5
        reasons.append("Bạn từng lưu nhà hàng này")
    if restaurant_id in user_profile.get("checked_in_ids", set()):
        score += 4
        reasons.append("Bạn từng check-in nhà hàng này")
    if restaurant_id in user_profile.get("reserved_ids", set()):
        score += 3
        reasons.append("Bạn từng đặt bàn ở đây")
    if restaurant_id in user_profile.get("reviewed_ids", set()):
        score += 3
        reasons.append("Bạn từng đánh giá tốt nhà hàng này")

    if set(tokenize(search_text)) & user_profile.get("recent_tokens", set()):
        score += 3
        reasons.append("Khớp xu hướng tìm kiếm gần đây của bạn")

    explicit_text = normalize_text(
        f"{restaurant.name} {restaurant.description or ''} {getattr(restaurant, 'cuisine_type', '')} {restaurant.address}"
    )
    if user_profile.get("preferred_cuisines") and any(item in explicit_text for item in user_profile["preferred_cuisines"]):
        score += 3
        reasons.append("Khớp sở thích ẩm thực trong hồ sơ")
    if user_profile.get("preferred_locations") and any(item in explicit_text for item in user_profile["preferred_locations"]):
        score += 2
        reasons.append("Khớp khu vực bạn thường quan tâm")

    return score, reasons[0] if reasons else ""


def _restaurant_ids(rows: list[Any]) -> set[str]:
    return {str(row.restaurant_id) for row in rows}
