from __future__ import annotations

import math
import re
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
from services.ai_assistant.tools import (
    available_menu_text,
    check_available_slots_tool,
    parse_price_range,
    price_budget_label,
    restaurant_matches_dish,
)
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
        return _select_diverse_results(scored, limit, intent), len(scored)

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
        lexical_reason = ""
        if lexical_score:
            score += 32 * lexical_score
            lexical_reason = _keyword_reason(query_tokens, restaurant_tokens)

        dish_score, dish_reason = _dish_score(intent, restaurant)
        if dish_score:
            score += dish_score
            explanations.append(dish_reason)

        cuisine_score = _cuisine_score(intent, restaurant, search_text)
        if cuisine_score:
            score += cuisine_score
            explanations.append(_cuisine_reason(intent, restaurant, search_text))
        elif intent_value(intent, "cuisines", []) or []:
            score -= 18

        semantic_score, semantic_reason = _semantic_score(intent, search_text)
        if semantic_score:
            score += semantic_score
            explanations.append(semantic_reason)

        preference_score, preference_reason = _preference_score(intent, search_text)
        if preference_score:
            score += preference_score
            explanations.append(preference_reason)

        if lexical_reason:
            explanations.append(lexical_reason)

        district_score = _district_score(intent, restaurant.address)
        if district_score:
            score += district_score
            explanations.append("Phù hợp khu vực được nhắc tới")

        budget_score = _budget_score(intent, restaurant.price_range)
        if budget_score:
            score += budget_score
            explanations.append(_budget_reason(restaurant.price_range))

        distance_km = _distance_from_user(latitude, longitude, restaurant)
        if distance_km is not None:
            score += max(0.0, 16 - min(distance_km, 16))
            explanations.append(_distance_reason(distance_km))

        rating = float(restaurant.rating_avg or 0)
        if rating > 0:
            score += min(rating, 5) * 3
            if rating >= 4.3:
                explanations.append(f"Điểm đánh giá nổi bật {rating:.1f}/5")

        quality_signals = get_restaurant_signals(db, restaurant)
        if quality_signals.quality_score:
            score += quality_signals.quality_score * 8
            explanations.extend(quality_signals.quality_reasons)
        if "less_popular" in (intent_value(intent, "preference_tags", []) or []) and quality_signals.favorite_count <= 2:
            score += 8
            explanations.append("Ít phổ biến hơn các lựa chọn quen thuộc")

        behavior_score, behavior_reason = user_behavior_score(restaurant, user_profile, search_text)
        if behavior_score:
            score += behavior_score
            explanations.insert(0, behavior_reason)

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
            available_menu_text(restaurant),
        ]
    )


def _overlap_score(query_tokens: set[str], restaurant_tokens: set[str]) -> float:
    if not query_tokens or not restaurant_tokens:
        return 0.0
    overlap = len(query_tokens & restaurant_tokens)
    return overlap / math.sqrt(len(query_tokens) * len(restaurant_tokens))


def _dish_score(intent: Any, restaurant: Restaurant) -> tuple[float, str]:
    matches = [
        dish
        for dish in (intent_value(intent, "dish_terms", []) or [])
        if restaurant_matches_dish(restaurant, dish)
    ]
    if not matches:
        return 0.0, ""
    return 32.0, "Có món " + ", ".join(matches[:2])


def _keyword_reason(query_tokens: set[str], restaurant_tokens: set[str]) -> str:
    useful_tokens = [
        token
        for token in query_tokens & restaurant_tokens
        if token
        not in {
            "mon",
            "quan",
            "ca",
            "cafe",
            "coffee",
            "nha",
            "hang",
            "han",
            "ban",
            "nghi",
            "nen",
            "an",
            "gi",
            "ky",
            "tuc",
            "xa",
            "ktx",
            "lang",
            "linh",
            "trung",
            "khu",
            "gan",
            "trong",
            "duoi",
            "hoc",
            "dai",
            "khoa",
            "tu",
            "nhien",
            "yen",
            "tinh",
            "cam",
            "wifi",
        }
        and not re.fullmatch(r"\d+(?:km|m|k)?", token)
    ]
    if not useful_tokens:
        return ""
    return "Khớp các chi tiết: " + ", ".join(sorted(useful_tokens)[:4])


def _cuisine_score(intent: Any, restaurant: Restaurant, search_text: str) -> float:
    requested_cuisines = intent_value(intent, "cuisines", []) or []
    if not requested_cuisines:
        requested_cuisines = _safe_infer_cuisines(search_text)
        return 0.0 if not requested_cuisines else 4.0

    explicit_text = normalize_text(f"{restaurant.name} {getattr(restaurant, 'cuisine_type', '')}")
    normalized = normalize_text(search_text)
    for cuisine in requested_cuisines:
        normalized_cuisine = normalize_text(cuisine)
        if _contains_alias(explicit_text, normalized_cuisine):
            return 36.0
        if any(_contains_alias(explicit_text, token) for token in _cuisine_aliases(normalized_cuisine)):
            return 34.0
        if _contains_alias(normalized, normalized_cuisine):
            return 10.0
    inferred = _safe_infer_cuisines(search_text)
    return 8.0 if set(map(normalize_text, requested_cuisines)) & set(map(normalize_text, inferred)) else 0.0


def _cuisine_reason(intent: Any, restaurant: Restaurant, search_text: str) -> str:
    requested_cuisines = intent_value(intent, "cuisines", []) or []
    if requested_cuisines:
        return f"Đúng nhóm {_display_cuisine_list(requested_cuisines)}"
    inferred = _safe_infer_cuisines(search_text)
    if inferred:
        return f"Phù hợp nhóm {_display_cuisine_list(inferred)}"
    return "Đúng nhóm món bạn đang tìm"


def _display_cuisine_list(cuisines: list[str]) -> str:
    labels = {
        "món hàn": "món Hàn",
        "món nhật": "món Nhật",
        "món thái": "món Thái",
        "món ý": "món Ý",
        "món việt": "món Việt",
        "món trung hoa": "món Trung Hoa",
        "chay / healthy": "chay / healthy",
        "cà phê / brunch": "cà phê / brunch",
    }
    return ", ".join(labels.get(cuisine, cuisine) for cuisine in cuisines[:2])


def _safe_infer_cuisines(search_text: str) -> list[str]:
    if not infer_cuisines:
        return []
    inferred = infer_cuisines(search_text)
    normalized = normalize_text(search_text)
    filtered: list[str] = []
    for cuisine in inferred:
        if cuisine == "món việt" and not _has_real_vietnamese_signal(normalized):
            continue
        if cuisine == "món trung hoa" and not _has_real_chinese_signal(normalized):
            continue
        filtered.append(cuisine)
    return filtered


def _has_real_vietnamese_signal(normalized_text: str) -> bool:
    strong_patterns = ["viet", "com nha", "quan com", "bun", "hu tieu", "banh cuon", "banh xeo"]
    if any(_contains_alias(normalized_text, pattern) for pattern in strong_patterns):
        return True
    return re.search(r"(?<!thanh )\bpho\b", normalized_text) is not None


def _has_real_chinese_signal(normalized_text: str) -> bool:
    strong_patterns = ["trung hoa", "dim sum", "sieu cay trung", "lau trung", "chinese"]
    return any(_contains_alias(normalized_text, pattern) for pattern in strong_patterns)


def _cuisine_aliases(normalized_cuisine: str) -> list[str]:
    aliases = {
        "ca phe brunch": ["cafe", "coffee", "ca phe", "tra sua", "brunch"],
        "lau": ["lau", "hotpot"],
        "bbq nuong": ["bbq", "nuong", "grill"],
        "mon nhat": ["nhat", "sushi", "ramen", "udon"],
        "mon han": ["han quoc", "korean", "kimchi", "tokbokki", "tteokbokki", "mi cay", "seoul", "daegu"],
        "hai san": ["hai san", "seafood", "oc"],
        "chay healthy": ["chay", "healthy", "salad"],
    }
    return aliases.get(normalized_cuisine, [])


def _contains_alias(normalized_text: str, alias: str) -> bool:
    normalized_alias = normalize_text(alias)
    if not normalized_alias:
        return False
    return re.search(rf"\b{re.escape(normalized_alias)}\b", normalized_text) is not None


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
    return min(18.0, 8.0 + len(overlap) * 5.0), _semantic_reason(overlap)


def _semantic_reason(tags: set[str]) -> str:
    reason_by_tag = {
        "yen_tinh": "Không gian yên tĩnh, hợp học bài/làm việc",
        "o_cam": "Có ổ cắm cho laptop/điện thoại",
        "wifi": "Có wifi, tiện ngồi học hoặc làm việc",
        "lam_viec": "Phù hợp ngồi làm việc laptop",
        "hen_ho": "Không gian hợp hẹn hò/nói chuyện riêng tư",
        "nhom_dong": "Phù hợp đi nhóm",
        "view_dep": "Có không gian/view dễ chịu",
        "do_xe": "Có yếu tố thuận tiện gửi xe",
        "troi_mua": "Hợp ngồi lại khi trời mưa",
    }
    reasons = [reason_by_tag[tag] for tag in sorted(tags) if tag in reason_by_tag]
    return ". ".join(reasons[:2]) if reasons else "Hợp vibe/nhu cầu bạn mô tả"


def _preference_score(intent: Any, search_text: str) -> tuple[float, str]:
    normalized = normalize_text(search_text)
    requested_tags = intent_value(intent, "preference_tags", []) or []
    patterns_by_tag = {
        "easy_to_eat": ["com", "bun", "pho", "banh", "chay", "can tin"],
        "light_meal": ["an nhe", "nhe bung", "chay", "salad", "banh", "tra sua", "cafe", "an vat"],
        "healthy": ["healthy", "chay", "salad", "rau", "eat clean", "thanh dam"],
        "filling": ["com", "lau", "buffet", "bun", "pho", "mi", "ga", "thit"],
        "quick_service": ["an nhanh", "phuc vu nhanh", "len mon nhanh", "can tin", "com", "banh mi"],
        "comfort_food": ["com", "pho", "bun", "lau", "mi", "am bung"],
        "cooling_food": ["tra sua", "nuoc", "kem", "salad", "cafe", "giai nhiet"],
        "vegetarian_option": ["chay", "healthy", "salad", "rau", "vegetarian"],
        "kid_friendly": ["tre em", "gia dinh", "kids"],
        "group_work": ["wifi", "o cam", "hoc nhom", "lam viec", "meeting"],
        "outdoor_seating": ["ngoai troi", "san vuon", "ban cong", "terrace"],
        "parking": ["do xe", "giu xe", "bai xe", "parking", "xe may"],
        "soupy_food": ["pho", "bun", "hu tieu", "lau", "canh", "mi", "sup", "soup", "bo kho"],
    }
    reason_by_tag = {
        "easy_to_eat": "Ưu tiên món dễ ăn",
        "light_meal": "Hợp nhu cầu ăn nhẹ",
        "healthy": "Có lựa chọn thiên về healthy",
        "filling": "Ưu tiên món giúp no bụng",
        "quick_service": "Phù hợp nhu cầu ăn nhanh",
        "comfort_food": "Hợp kiểu comfort food dễ ăn",
        "cooling_food": "Có lựa chọn mát và dễ dùng khi trời nóng",
        "vegetarian_option": "Có lựa chọn phù hợp người ăn chay",
        "kid_friendly": "Phù hợp nhóm có trẻ em",
        "group_work": "Phù hợp ngồi làm việc nhóm",
        "outdoor_seating": "Có yếu tố không gian ngoài trời",
        "parking": "Thuận tiện cho nhóm đi xe máy",
        "soupy_food": "Ưu tiên món nước",
    }
    hits = [
        tag
        for tag in requested_tags
        if tag in patterns_by_tag and any(_contains_alias(normalized, pattern) for pattern in patterns_by_tag[tag])
    ]
    if not hits:
        if any(tag in requested_tags for tag in ["healthy", "light_meal", "vegetarian_option", "cooling_food"]):
            return -12.0, ""
        return 0.0, ""
    return min(18.0, 6.0 + len(hits) * 4.0), ". ".join(reason_by_tag[tag] for tag in hits[:2])


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


def _budget_reason(price_range: str | None) -> str:
    price_min, price_max = parse_price_range(price_range)
    if price_min is not None and price_max is not None:
        return f"Khoảng giá khoảng {price_min // 1000}k-{price_max // 1000}k"
    if price_max is not None:
        return f"Giá khoảng {price_max // 1000}k"
    return "Mức giá hợp với ngân sách"


def _distance_reason(distance_km: float) -> str:
    if distance_km < 0.2:
        return f"Rất gần điểm demo, khoảng {distance_km:.1f} km"
    if distance_km < 1:
        return f"Đi bộ/di chuyển ngắn, khoảng {distance_km:.1f} km"
    return f"Cách điểm tìm kiếm khoảng {distance_km:.1f} km"


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


def _select_diverse_results(scored: list[ScoredRestaurant], limit: int, intent: Any) -> list[ScoredRestaurant]:
    if limit <= 0 or len(scored) <= limit:
        return scored[:limit]

    explicit_food_request = bool(intent_value(intent, "cuisines", []) or intent_value(intent, "dish_terms", []))
    max_per_cuisine = limit if explicit_food_request else max(1, min(2, limit // 2))

    selected: list[ScoredRestaurant] = []
    used_ids: set[str] = set()
    used_name_families: set[str] = set()
    cuisine_counts: dict[str, int] = {}

    def try_add(item: ScoredRestaurant, *, enforce_cuisine: bool, enforce_family: bool) -> None:
        if len(selected) >= limit:
            return
        restaurant_id = str(item.restaurant.restaurant_id)
        if restaurant_id in used_ids:
            return
        name_family = _name_family_key(item.restaurant.name)
        cuisine_key = _primary_cuisine_key(item.restaurant)
        if enforce_family and name_family and name_family in used_name_families:
            return
        if enforce_cuisine and cuisine_key and cuisine_counts.get(cuisine_key, 0) >= max_per_cuisine:
            return
        selected.append(item)
        used_ids.add(restaurant_id)
        if name_family:
            used_name_families.add(name_family)
        if cuisine_key:
            cuisine_counts[cuisine_key] = cuisine_counts.get(cuisine_key, 0) + 1

    for item in scored:
        try_add(item, enforce_cuisine=True, enforce_family=True)
    for item in scored:
        try_add(item, enforce_cuisine=False, enforce_family=True)
    for item in scored:
        try_add(item, enforce_cuisine=False, enforce_family=False)

    return selected[:limit]


def _name_family_key(name: str | None) -> str:
    normalized = normalize_text(name)
    if not normalized:
        return ""
    normalized = re.sub(
        r"\b(?:quan|nha hang|cafe|ca phe|tra sua|chi nhanh|co so|cn|thu duc|di an|linh trung|lang dai hoc)\b",
        " ",
        normalized,
    )
    normalized = re.sub(r"\b(?:duong|hem|so|quan|phuong)\b.*$", " ", normalized)
    tokens = [token for token in normalized.split() if token and not token.isdigit()]
    return " ".join(tokens[:3])


def _primary_cuisine_key(restaurant: Restaurant) -> str:
    category_names = [
        normalize_text(link.category.name)
        for link in (getattr(restaurant, "cuisine_links", []) or [])
        if getattr(link, "category", None) is not None and getattr(link.category, "name", None)
    ]
    if category_names:
        return category_names[0]
    inferred = _safe_infer_cuisines(restaurant_search_text(restaurant))
    if inferred:
        return normalize_text(inferred[0])
    return normalize_text(getattr(restaurant, "cuisine_type", "") or "")
