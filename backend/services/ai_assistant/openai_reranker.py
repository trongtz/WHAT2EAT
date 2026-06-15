from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from core.config import settings
from services.ai_assistant.intent_extractor import intent_to_dict
from services.ai_assistant.openai_response_client import OpenAIResponsesError, request_structured_json


RERANK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "assistant_message": {"type": "string"},
        "ranked_results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "reason"],
            },
        },
    },
    "required": ["assistant_message", "ranked_results"],
}


class AgenticRerankError(RuntimeError):
    pass


@dataclass
class AgenticRerankResult:
    matches: list[Any]
    assistant_message: str


def should_use_agentic_reranker() -> bool:
    return bool(settings.OPENAI_AGENTIC_RERANKER and settings.OPENAI_API_KEY)


def agentic_shortlist_size(limit: int) -> int:
    return max(limit, min(max(settings.OPENAI_RERANK_SHORTLIST_SIZE, 5), 20))


def rerank_shortlist(
    *,
    query: str,
    intent: Any,
    recent_user_queries: list[str],
    matches: list[Any],
    limit: int,
) -> AgenticRerankResult:
    if not matches:
        return AgenticRerankResult(matches=[], assistant_message="")

    shortlisted_matches = matches[:agentic_shortlist_size(limit)]
    match_by_id = {str(match.restaurant.restaurant_id): match for match in shortlisted_matches}
    payload = {
        "task": "Rerank a filtered restaurant shortlist and write a concise Vietnamese chat response.",
        "rules": [
            "Only use restaurant IDs present in candidates.",
            "Never invent a restaurant, menu item, price, location, or amenity.",
            "Hard constraints were already applied. Prefer semantic fit, user context, distance, quality, and capacity.",
            "When candidates are similarly relevant, prefer diversity across restaurant names, chains, cuisine styles, and menu types.",
            "Do not collapse to only the nearest restaurant unless it is clearly the only good match.",
            f"Return at most {limit} ranked results.",
            f"If at least {limit} candidates are reasonable, return {limit} ranked results.",
            "assistant_message must be concise, natural Vietnamese and must not enumerate restaurants because the UI renders the list.",
            "Each reason must mention the most relevant evidence for that specific result.",
        ],
        "query": query,
        "intent": intent_to_dict(intent),
        "recent_user_queries": [str(item)[:300] for item in recent_user_queries[-6:]],
        "candidates": [_candidate_payload(match) for match in shortlisted_matches],
    }
    try:
        parsed = request_structured_json(
            schema_name="restaurant_rerank",
            schema=RERANK_SCHEMA,
            payload=payload,
            instructions=(
                "You are a restaurant recommendation reranker. Use only supplied candidate evidence. "
                "Return the requested structured JSON in Vietnamese."
            ),
        )
    except OpenAIResponsesError as exc:
        raise AgenticRerankError(str(exc)) from exc

    ranked_matches: list[Any] = []
    used_ids: set[str] = set()
    for item in parsed.get("ranked_results", []) or []:
        restaurant_id = str(item.get("id") or "")
        if restaurant_id in used_ids or restaurant_id not in match_by_id:
            continue
        reason = str(item.get("reason") or "").strip()
        if not reason:
            continue
        ranked_matches.append(replace(match_by_id[restaurant_id], reason=reason[:500]))
        used_ids.add(restaurant_id)
        if len(ranked_matches) >= limit:
            break

    if not ranked_matches:
        raise AgenticRerankError("OpenAI reranker returned no valid restaurant IDs.")

    for match in shortlisted_matches:
        if len(ranked_matches) >= limit:
            break
        restaurant_id = str(match.restaurant.restaurant_id)
        if restaurant_id not in used_ids:
            ranked_matches.append(match)
            used_ids.add(restaurant_id)

    assistant_message = str(parsed.get("assistant_message") or "").strip()[:700]
    return AgenticRerankResult(matches=ranked_matches, assistant_message=assistant_message)


def _candidate_payload(match: Any) -> dict[str, Any]:
    restaurant = match.restaurant
    menu_highlights = [
        item.name
        for item in (getattr(restaurant, "menu_items", []) or [])
        if getattr(item, "availability_status", "AVAILABLE") == "AVAILABLE"
    ][:8]
    return {
        "id": str(restaurant.restaurant_id),
        "name": restaurant.name,
        "address": restaurant.address,
        "cuisine": getattr(restaurant, "cuisine_type", "") or "",
        "price_range": restaurant.price_range,
        "distance_km": match.distance_km,
        "available_capacity": match.available_capacity,
        "quality_score": round(match.quality_score, 4),
        "quality_signals": match.quality_signals,
        "menu_highlights": menu_highlights,
        "offline_score": round(match.score, 4),
        "offline_reason": match.reason,
    }
