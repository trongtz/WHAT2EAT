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
) -> dict[str, Any]:
    return {
        "message": build_message(query, matches, intent),
        "total_found": total_found,
        "filters_applied": filters_applied,
        "result_restaurant_ids": [str(match.restaurant.restaurant_id) for match in matches],
        "recommended_restaurants": [
            {
                "id": str(match.restaurant.restaurant_id),
                "name": match.restaurant.name,
                "address": match.restaurant.address,
                "distance_km": match.distance_km,
                "match_score": round(min(match.score / 100, 1.0), 4),
                "reason": match.reason,
                "available_capacity": match.available_capacity,
            }
            for match in matches
        ],
        "source": "HYBRID",
    }


def build_message(query: str, matches: list[ScoredRestaurant], intent: Any) -> str:
    if not matches:
        return "Mình chưa tìm thấy nhà hàng thật sự khớp. Bạn thử nói rõ hơn khu vực, món ăn hoặc ngân sách nhé."

    cuisine_text = ", ".join(intent_value(intent, "cuisines", []) or [])
    district_text = ", ".join(intent_value(intent, "districts", []) or [])
    context = " theo mô tả của bạn"
    if cuisine_text and district_text:
        context = f" cho món {cuisine_text} ở {district_text}"
    elif cuisine_text:
        context = f" cho món {cuisine_text}"
    elif district_text:
        context = f" gần {district_text}"

    return f"Mình tìm được {len(matches)} gợi ý{context}. Kết quả được xếp hạng bằng recommend system dựa trên intent, từ khóa, giá, vị trí và điểm đánh giá."
