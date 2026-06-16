from __future__ import annotations

from typing import Any

from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommendation_engine import ScoredRestaurant


def compose_recommendation_response(
    *,
    query: str,
    matches: list[ScoredRestaurant],
    total_found: int,
    intent: Any,
    filters_applied: dict[str, Any],
    message_override: str | None = None,
    source: str = "HYBRID",
) -> dict[str, Any]:
    return {
        "message": message_override or build_message(query, matches, intent),
        "total_found": total_found,
        "filters_applied": filters_applied,
        "result_restaurant_ids": [str(match.restaurant.restaurant_id) for match in matches],
        "recommended_restaurants": [
            {
                "id": str(match.restaurant.restaurant_id),
                "name": match.restaurant.name,
                "address": match.restaurant.address,
                "images": [image for image in (match.restaurant.images or []) if image],
                "image": next((image for image in (match.restaurant.images or []) if image), ""),
                "average_rating": float(match.restaurant.rating_avg or 0),
                "distance_km": match.distance_km,
                "match_score": round(min(match.score / 100, 1.0), 4),
                "reason": match.reason,
                "available_capacity": match.available_capacity,
                "quality_score": match.quality_score,
                "availability_score": match.availability_score,
                "quality_signals": match.quality_signals,
            }
            for match in matches
        ],
        "source": source,
    }


def build_message(query: str, matches: list[ScoredRestaurant], intent: Any) -> str:
    prefix = _build_intent_prefix(intent)
    if not matches:
        return prefix + _build_empty_result_message(intent)

    cuisine_text = _display_cuisine_text(intent_value(intent, "cuisines", []) or [])
    dish_text = ", ".join(intent_value(intent, "dish_terms", []) or [])
    district_text = ", ".join(intent_value(intent, "districts", []) or [])
    context = " theo mô tả của bạn"
    if cuisine_text and district_text:
        context = f" cho {cuisine_text} ở {district_text}"
    elif cuisine_text:
        context = f" cho {cuisine_text}"
    elif dish_text:
        context = f" có {dish_text}"
    elif district_text:
        context = f" gần {district_text}"

    return prefix + f"Mình tìm được {len(matches)} gợi ý{context}. Kết quả đã tính theo nhu cầu, vị trí, chất lượng quán và tình trạng còn chỗ."


def _build_empty_result_message(intent: Any) -> str:
    preference_tags = intent_value(intent, "preference_tags", []) or []
    excluded_keywords = intent_value(intent, "excluded_keywords", []) or []
    excluded_cuisines = intent_value(intent, "excluded_cuisines", []) or []
    dish_terms = intent_value(intent, "dish_terms", []) or []

    if "light_meal" in preference_tags and any(keyword in excluded_keywords for keyword in ["com", "cơm"]):
        return (
            "Mình đang ưu tiên món ăn nhẹ và tránh cơm theo ngữ cảnh bạn vừa nói, "
            "nhưng hiện chưa tìm thấy quán phù hợp trong khu vực này. "
            "Mình không bù bằng quán cơm hoặc món nặng bụng để tránh gợi ý sai nhu cầu."
        )
    if excluded_cuisines or excluded_keywords:
        exclusions = [*excluded_cuisines, *excluded_keywords]
        return (
            "Mình đã giữ các điều kiện cần tránh như "
            + ", ".join(exclusions[:3])
            + ", nhưng hiện chưa tìm thấy quán thật sự phù hợp. "
            "Bạn có thể nới lỏng một điều kiện hoặc thử khu vực khác."
        )
    if dish_terms:
        return (
            "Mình hiểu bạn đang tìm "
            + ", ".join(dish_terms[:2])
            + ", nhưng hiện chưa tìm thấy quán phù hợp trong khu vực này. "
            "Mình không bù bằng quán chỉ khớp một phần để tránh gợi ý sai món."
        )
    return "Mình chưa tìm thấy nhà hàng thật sự khớp. Bạn thử nới lỏng một tiêu chí hoặc nói rõ hơn khu vực nhé."


def _display_cuisine_text(cuisines: list[str]) -> str:
    labels = {
        "món hàn": "món Hàn",
        "món nhật": "món Nhật",
        "món thái": "món Thái",
        "món ý": "món Ý",
        "món việt": "món Việt",
        "cà phê / brunch": "cà phê / brunch",
    }
    return ", ".join(labels.get(cuisine, cuisine) for cuisine in cuisines)


def _build_intent_prefix(intent: Any) -> str:
    parts: list[str] = []
    conflicts = intent_value(intent, "conflicts", []) or []
    if conflicts:
        parts.append("Lưu ý: " + " ".join(conflicts[:2]))

    excluded_cuisines = intent_value(intent, "excluded_cuisines", []) or []
    excluded_keywords = intent_value(intent, "excluded_keywords", []) or []
    if excluded_cuisines or excluded_keywords:
        exclusions = [*excluded_cuisines, *excluded_keywords]
        parts.append("Mình đã tránh các lựa chọn liên quan đến " + ", ".join(exclusions[:3]) + ".")

    preference_tags = intent_value(intent, "preference_tags", []) or []
    preference_labels = {
        "easy_to_eat": "món dễ ăn",
        "light_meal": "món nhẹ bụng",
        "healthy": "healthy",
        "filling": "món no bụng",
        "less_popular": "quán ít phổ biến hơn",
        "quick_service": "phục vụ nhanh",
        "comfort_food": "comfort food",
        "cooling_food": "món giúp giải nhiệt",
        "hot_food": "món nóng",
        "vegetarian_option": "lựa chọn cho người ăn chay",
        "kid_friendly": "chỗ phù hợp trẻ em",
        "group_work": "chỗ hợp làm việc nhóm",
        "outdoor_seating": "chỗ ngồi ngoài trời",
        "parking": "chỗ thuận tiện gửi xe",
        "soupy_food": "món nước",
    }
    readable_preferences = [preference_labels[tag] for tag in preference_tags if tag in preference_labels]
    if readable_preferences:
        parts.append("Mình đang ưu tiên " + ", ".join(readable_preferences[:3]) + ".")

    return (" ".join(parts) + " ") if parts else ""
