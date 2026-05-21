from __future__ import annotations

from typing import Any

from services.ai_assistant.recommend_imports import parse_query_heuristically, tokenize


def extract_intent(query: str, previous_query: str | None = None) -> Any:
    intent = parse_query_heuristically(query) if parse_query_heuristically else _fallback_intent(query)
    if not previous_query:
        return intent

    previous_intent = parse_query_heuristically(previous_query) if parse_query_heuristically else _fallback_intent(previous_query)
    if hasattr(intent, "merged_with"):
        return intent.merged_with(previous_intent)

    merged = dict(previous_intent)
    merged.update({key: value for key, value in intent.items() if value not in (None, [], "")})
    return merged


def intent_value(intent: Any, key: str, default: Any = None) -> Any:
    if isinstance(intent, dict):
        return intent.get(key, default)
    return getattr(intent, key, default)


def intent_to_dict(intent: Any) -> dict[str, Any]:
    if hasattr(intent, "to_dict"):
        return intent.to_dict()
    if isinstance(intent, dict):
        return intent
    return {}


def filters_from_intent(intent: Any) -> dict[str, Any]:
    return {
        "cuisines": intent_value(intent, "cuisines", []) or [],
        "districts": intent_value(intent, "districts", []) or [],
        "ambience_tags": intent_value(intent, "ambience_tags", []) or [],
        "amenity_tags": intent_value(intent, "amenity_tags", []) or [],
        "occasion_tags": intent_value(intent, "occasion_tags", []) or [],
        "weather_tags": intent_value(intent, "weather_tags", []) or [],
        "price_min": intent_value(intent, "price_min"),
        "price_max": intent_value(intent, "price_max"),
        "budget_label": intent_value(intent, "budget_label"),
        "group_size": intent_value(intent, "group_size"),
        "open_now": intent_value(intent, "open_now"),
    }


def _fallback_intent(query: str) -> dict[str, Any]:
    return {
        "keywords": tokenize(query),
        "cuisines": [],
        "districts": [],
        "ambience_tags": [],
        "amenity_tags": [],
        "occasion_tags": [],
        "weather_tags": [],
        "price_min": None,
        "price_max": None,
        "budget_label": None,
        "group_size": None,
        "open_now": None,
    }
