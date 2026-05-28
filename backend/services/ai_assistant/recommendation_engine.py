from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models.restaurant import Restaurant
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommend_imports import (
    extract_district_slug_from_text,
    haversine_km,
    infer_cuisines,
    infer_semantic_tags,
    normalize_text,
    tokenize,
)
from services.ai_assistant.tools import check_available_slots_tool, parse_price_range, price_budget_label
from services.ai_assistant.restaurant_signals import availability_score, get_restaurant_signals
from services.ai_assistant.user_preferences import user_behavior_score


@dataclass
class ScoredRestaurant:
    restaurant: Restaurant
    score: float
    reason: str
    distance_km: float | None
    available_capacity: int | None
    quality_score: float = 0.0
    availability_score: float = 0.0
    quality_signals: dict[str, Any] | None = None


class RecommendationEngine:
    def rank_restaurants_tool(
        self,
        db: Session,
        *,
        candidate_restaurants: list[Restaurant],
        intent: Any,
        query: str,
        latitude: float | None,
        longitude: float | None,
        user_profile: dict[str, Any],
        limit: int,
    ) -> tuple[list[ScoredRestaurant], int]:
        scored = [
            scored_restaurant
            for restaurant in candidate_restaurants
            if (
                scored_restaurant := self._score_restaurant(
                    db,
                    restaurant,
                    intent,
                    query,
                    latitude,
                    longitude,
                    user_profile,
                )
            ).score
            > 0
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit], len(scored)

    def _score_restaurant(
        self,
        db: Session,
        restaurant: Restaurant,
        intent: Any,
        query: str,
        latitude: float | None,
        longitude: float | None,
        user_profile: dict[str, Any],
    ) -> ScoredRestaurant:
        search_text = restaurant_search_text(restaurant)
        restaurant_tokens = set(tokenize(search_text))
        query_tokens = set(intent_value(intent, "keywords", []) or tokenize(query))
        explanations: list[str] = []
        score = 0.0

        lexical_score = _overlap_score(query_tokens, restaurant_tokens)
        if lexical_score:
            score += 32 * lexical_score
            explanations.append("Khớp từ khóa trong mô tả nhà hàng")

        cuisine_score = _cuisine_score(intent, restaurant, search_text)
        if cuisine_score:
            score += cuisine_score
            explanations.append("Đúng nhóm món bạn đang tìm")
        elif intent_value(intent, "cuisines", []) or []:
            score -= 18

        semantic_score, semantic_reason = _semantic_score(intent, search_text)
        if semantic_score:
            score += semantic_score
            explanations.append(semantic_reason)

        district_score = _district_score(intent, restaurant.address)
        if district_score:
            score += district_score
            explanations.append("Phù hợp khu vực được nhắc tới")

        budget_score = _budget_score(intent, restaurant.price_range)
        if budget_score:
            score += budget_score
            explanations.append("Mức giá hợp với ngân sách")

        distance_km = _distance_from_user(latitude, longitude, restaurant)
        if distance_km is not None:
            score += max(0.0, 16 - min(distance_km, 16))
            explanations.append(f"Cách bạn khoảng {distance_km:.1f} km")

        rating = float(restaurant.rating_avg or 0)
        if rating > 0:
            score += min(rating, 5) * 3
            if rating >= 4.3:
                explanations.append("Điểm đánh giá đang tốt")

        quality_signals = get_restaurant_signals(db, restaurant)
        if quality_signals.quality_score:
            score += quality_signals.quality_score * 8
            explanations.extend(quality_signals.quality_reasons)

        behavior_score, behavior_reason = user_behavior_score(restaurant, user_profile, search_text)
        if behavior_score:
            score += behavior_score
            explanations.append(behavior_reason)

        available_capacity = check_available_slots_tool(db, restaurant)
        group_size = intent_value(intent, "group_size")
        normalized_group_size = int(group_size) if group_size is not None else None
        availability_value, availability_reasons = availability_score(available_capacity, normalized_group_size)
        if availability_value:
            score += availability_value * 7
            explanations.extend(availability_reasons)

        if not explanations and score == 0:
            score = rating
            explanations.append("Gợi ý dựa trên điểm đánh giá tổng thể")

        return ScoredRestaurant(
            restaurant=restaurant,
            score=score,
            reason=_join_reason(explanations),
            distance_km=round(distance_km, 2) if distance_km is not None else None,
            available_capacity=available_capacity,
            quality_score=quality_signals.quality_score,
            availability_score=round(availability_value, 4),
            quality_signals={
                "rating_avg": quality_signals.rating_avg,
                "rating_count": quality_signals.rating_count,
                "checkin_count_30d": quality_signals.checkin_count_30d,
                "favorite_count": quality_signals.favorite_count,
                "booking_count_30d": quality_signals.booking_count_30d,
            },
        )


def restaurant_search_text(restaurant: Restaurant) -> str:
    cuisine_text = getattr(restaurant, "cuisine_type", "") or ""
    return " ".join(
        str(part or "")
        for part in [
            restaurant.name,
            restaurant.description,
            restaurant.address,
            cuisine_text,
            restaurant.price_range,
        ]
    )


def _overlap_score(query_tokens: set[str], restaurant_tokens: set[str]) -> float:
    if not query_tokens or not restaurant_tokens:
        return 0.0
    overlap = len(query_tokens & restaurant_tokens)
    return overlap / math.sqrt(len(query_tokens) * len(restaurant_tokens))


def _cuisine_score(intent: Any, restaurant: Restaurant, search_text: str) -> float:
    requested_cuisines = intent_value(intent, "cuisines", []) or []
    if not requested_cuisines:
        requested_cuisines = infer_cuisines(search_text) if infer_cuisines else []
        return 0.0 if not requested_cuisines else 4.0

    explicit_text = normalize_text(f"{restaurant.name} {getattr(restaurant, 'cuisine_type', '')}")
    normalized = normalize_text(search_text)
    for cuisine in requested_cuisines:
        normalized_cuisine = normalize_text(cuisine)
        if normalized_cuisine in explicit_text:
            return 36.0
        if any(token in explicit_text for token in _cuisine_aliases(normalized_cuisine)):
            return 34.0
        if normalized_cuisine in normalized:
            return 10.0
    inferred = infer_cuisines(search_text) if infer_cuisines else []
    return 8.0 if set(map(normalize_text, requested_cuisines)) & set(map(normalize_text, inferred)) else 0.0


def _cuisine_aliases(normalized_cuisine: str) -> list[str]:
    aliases = {
        "ca phe brunch": ["cafe", "coffee", "ca phe", "tra sua", "brunch"],
        "lau": ["lau", "hotpot"],
        "bbq nuong": ["bbq", "nuong", "grill"],
        "mon nhat": ["nhat", "sushi", "ramen", "udon"],
        "mon han": ["han", "korean", "kimchi", "tokbokki"],
        "hai san": ["hai san", "seafood", "oc"],
        "chay healthy": ["chay", "healthy", "salad"],
    }
    return aliases.get(normalized_cuisine, [])


def _semantic_score(intent: Any, search_text: str) -> tuple[float, str]:
    requested_tags = [
        *(intent_value(intent, "ambience_tags", []) or []),
        *(intent_value(intent, "amenity_tags", []) or []),
        *(intent_value(intent, "occasion_tags", []) or []),
        *(intent_value(intent, "weather_tags", []) or []),
    ]
    if not requested_tags or not infer_semantic_tags:
        return 0.0, ""

    overlap = set(requested_tags) & set(infer_semantic_tags(search_text))
    if not overlap:
        return 0.0, ""
    return min(18.0, 8.0 + len(overlap) * 5.0), "Hợp vibe/nhu cầu bạn mô tả"


def _district_score(intent: Any, address: str) -> float:
    requested_districts = set(intent_value(intent, "districts", []) or [])
    if not requested_districts:
        return 0.0
    restaurant_district = extract_district_slug_from_text(address)
    return 16.0 if restaurant_district in requested_districts else 0.0


def _budget_score(intent: Any, price_range: str | None) -> float:
    price_min, price_max = parse_price_range(price_range)
    if price_min is None and price_max is None:
        return 0.0

    requested_min = intent_value(intent, "price_min")
    requested_max = intent_value(intent, "price_max")
    budget_label = intent_value(intent, "budget_label")

    if requested_max is not None and price_min is not None and price_min <= requested_max:
        return 14.0
    if requested_min is not None and price_max is not None and price_max >= requested_min:
        return 10.0
    if budget_label and budget_label == price_budget_label(price_min, price_max):
        return 12.0
    return 0.0


def _distance_from_user(latitude: float | None, longitude: float | None, restaurant: Restaurant) -> float | None:
    if latitude is None or longitude is None:
        return None
    return haversine_km(latitude, longitude, _decimal_to_float(restaurant.latitude), _decimal_to_float(restaurant.longitude))


def _decimal_to_float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _join_reason(explanations: list[str]) -> str:
    unique_reasons = list(dict.fromkeys(reason for reason in explanations if reason))
    return ". ".join(unique_reasons[:3]) + ("." if unique_reasons else "")
