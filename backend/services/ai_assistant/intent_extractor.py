from __future__ import annotations

import re
from typing import Any

from services.ai_assistant.openai_intent_parser import (
    OpenAIIntentParserError,
    parse_intent_with_openai,
    should_use_openai_intent_parser,
)
from services.ai_assistant.recommend_imports import normalize_text, parse_query_heuristically, tokenize, unique_preserve_order


def extract_intent(query: str, previous_query: str | None = None) -> Any:
    if should_use_openai_intent_parser():
        try:
            parsed_intent = parse_intent_with_openai(query, previous_query=previous_query)
            return _merge_local_heuristics(parsed_intent, parse_query_heuristically(query))
        except OpenAIIntentParserError:
            pass

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
        "excluded_cuisines": intent_value(intent, "excluded_cuisines", []) or [],
        "excluded_keywords": intent_value(intent, "excluded_keywords", []) or [],
        "preference_tags": intent_value(intent, "preference_tags", []) or [],
        "dish_terms": intent_value(intent, "dish_terms", []) or [],
        "conflicts": intent_value(intent, "conflicts", []) or [],
        "walking_only": bool(intent_value(intent, "walking_only", False)),
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
        "excluded_cuisines": [],
        "excluded_keywords": [],
        "preference_tags": [],
        "dish_terms": [],
        "conflicts": [],
        "walking_only": False,
    }


def _merge_local_heuristics(openai_intent: dict[str, Any], local_intent: Any) -> dict[str, Any]:
    merged = dict(openai_intent)
    if _is_broad_recommendation(local_intent):
        # For vague prompts, GPT should help understand mood, not invent hard filters.
        merged["cuisines"] = []
        merged["dish_terms"] = []
    if _should_drop_model_food_guesses(local_intent):
        # Contextual prompts like weather/mood should not become a guessed cuisine.
        merged["cuisines"] = []
        merged["dish_terms"] = []
    if _uses_demo_location_anchor(local_intent) and not intent_value(local_intent, "districts", []):
        # Demo location words like KTX/Linh Trung are handled by coordinates, not HCMC district filters.
        merged["districts"] = []

    for key in (
        "cuisines",
        "districts",
        "ambience_tags",
        "amenity_tags",
        "occasion_tags",
        "weather_tags",
        "excluded_cuisines",
        "excluded_keywords",
        "preference_tags",
        "dish_terms",
        "conflicts",
    ):
        merged[key] = unique_preserve_order(
            [
                *(merged.get(key) or []),
                *(intent_value(local_intent, key, []) or []),
            ]
        )
    for key in ("price_min", "price_max", "budget_label", "group_size", "open_now"):
        if merged.get(key) is None:
            merged[key] = intent_value(local_intent, key)
    merged["walking_only"] = bool(merged.get("walking_only") or intent_value(local_intent, "walking_only", False))
    _sanitize_merged_intent(merged, local_intent)
    return merged


def _is_broad_recommendation(local_intent: Any) -> bool:
    if any(
        intent_value(local_intent, key)
        for key in (
            "cuisines",
            "districts",
            "ambience_tags",
            "amenity_tags",
            "occasion_tags",
            "weather_tags",
            "dish_terms",
            "excluded_cuisines",
            "excluded_keywords",
            "price_min",
            "price_max",
            "budget_label",
            "group_size",
            "open_now",
        )
    ):
        return False

    normalized = normalize_text(intent_value(local_intent, "original_query", ""))
    broad_phrases = [
        "khong biet an gi",
        "nen an gi",
        "goi y mon de an",
        "an gi do ngon",
        "an gi do ngon ngon",
        "co gi an",
        "chan an",
    ]
    broad_tags = {"easy_to_eat", "comfort_food", "light_meal"}
    preference_tags = set(intent_value(local_intent, "preference_tags", []) or [])
    return any(phrase in normalized for phrase in broad_phrases) or bool(preference_tags & broad_tags)


def _should_drop_model_food_guesses(local_intent: Any) -> bool:
    if intent_value(local_intent, "cuisines", []) or intent_value(local_intent, "dish_terms", []):
        return False
    contextual_tags = [
        *(intent_value(local_intent, "weather_tags", []) or []),
        *(intent_value(local_intent, "occasion_tags", []) or []),
    ]
    preference_tags = set(intent_value(local_intent, "preference_tags", []) or [])
    contextual_preferences = {
        "cooling_food",
        "comfort_food",
        "light_meal",
        "easy_to_eat",
        "kid_friendly",
        "group_work",
        "outdoor_seating",
        "parking",
    }
    return bool(contextual_tags) or bool(preference_tags & contextual_preferences)


def _sanitize_merged_intent(merged: dict[str, Any], local_intent: Any) -> None:
    normalized = normalize_text(intent_value(local_intent, "original_query", ""))
    if (
        merged.get("price_max") is not None
        and int(merged["price_max"]) < 1000
        and re.search(r"\b\d+(?:[.,]\d+)?\s*(?:m|km)\b", normalized)
    ):
        merged["price_max"] = None
        merged["notes"] = unique_preserve_order(
            [*(merged.get("notes") or []), "Đã bỏ price_max vì số này là khoảng cách, không phải ngân sách."]
        )

    _prefer_local_price_when_openai_drops_k_suffix(merged, local_intent, "price_min")
    _prefer_local_price_when_openai_drops_k_suffix(merged, local_intent, "price_max")

    local_group_size = intent_value(local_intent, "group_size")
    if (
        merged.get("group_size") == 1
        and local_group_size is None
        and "vegetarian_option" in (merged.get("preference_tags") or [])
    ):
        merged["group_size"] = None
        merged["notes"] = unique_preserve_order(
            [*(merged.get("notes") or []), "Đã bỏ group_size=1 vì câu nói về 1 người ăn chay trong nhóm."]
        )


def _prefer_local_price_when_openai_drops_k_suffix(merged: dict[str, Any], local_intent: Any, key: str) -> None:
    local_value = intent_value(local_intent, key)
    merged_value = merged.get(key)
    if local_value is None or merged_value is None:
        return
    if int(merged_value) < 1000 <= int(local_value):
        merged[key] = local_value
        merged["notes"] = unique_preserve_order(
            [*(merged.get("notes") or []), f"Đã chuẩn hóa {key} theo hậu tố k/nghìn trong câu hỏi."]
        )


def _uses_demo_location_anchor(local_intent: Any) -> bool:
    normalized = normalize_text(intent_value(local_intent, "original_query", ""))
    return any(
        keyword in normalized
        for keyword in [
            "ktx",
            "ky tuc xa",
            "linh trung",
            "lang dai hoc",
            "dhqg",
            "dai hoc quoc gia",
            "khoa hoc tu nhien",
            "dh khtn",
        ]
    )
