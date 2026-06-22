from __future__ import annotations

from typing import Any

from core.config import settings
from services.ai_assistant.openai_response_client import OpenAIResponsesError, request_structured_json
from services.ai_assistant.recommend_imports import (
    AMBIENCE_PATTERNS,
    AMENITY_PATTERNS,
    CUISINE_PATTERNS,
    DISH_PATTERNS,
    OCCASION_PATTERNS,
    PREFERENCE_PATTERNS,
    WEATHER_PATTERNS,
    normalize_text,
    tokenize,
    unique_preserve_order,
)


class OpenAIIntentParserError(RuntimeError):
    pass


ALLOWED_BUDGET_LABELS = {"binh_dan", "trung_binh", "kha_cao", "cao_cap"}
ALLOWED_CONTEXT_ACTIONS = {"fresh_search", "refine_previous", "switch_topic"}
ALLOWED_INTENT_TYPES = {
    "restaurant_search",
    "restaurant_followup",
    "booking_or_agent",
    "preference_update",
    "unclear",
    "out_of_domain",
}
ALLOWED_CLEAR_FIELDS = {
    "keywords",
    "cuisines",
    "districts",
    "ambience_tags",
    "amenity_tags",
    "occasion_tags",
    "weather_tags",
    "price_min",
    "price_max",
    "budget_label",
    "group_size",
    "open_now",
    "excluded_cuisines",
    "excluded_keywords",
    "preference_tags",
    "dish_terms",
    "conflicts",
}
INTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent_type": {
            "type": "string",
            "enum": [
                "restaurant_search",
                "restaurant_followup",
                "booking_or_agent",
                "preference_update",
                "unclear",
                "out_of_domain",
            ],
        },
        "context_action": {
            "type": "string",
            "enum": ["fresh_search", "refine_previous", "switch_topic"],
        },
        "clarification_message": {"type": ["string", "null"]},
        "clear_fields": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "cuisines": {"type": "array", "items": {"type": "string"}},
        "districts": {"type": "array", "items": {"type": "string"}},
        "ambience_tags": {"type": "array", "items": {"type": "string"}},
        "amenity_tags": {"type": "array", "items": {"type": "string"}},
        "occasion_tags": {"type": "array", "items": {"type": "string"}},
        "weather_tags": {"type": "array", "items": {"type": "string"}},
        "price_min": {"type": ["integer", "null"]},
        "price_max": {"type": ["integer", "null"]},
        "budget_label": {"type": ["string", "null"]},
        "group_size": {"type": ["integer", "null"]},
        "open_now": {"type": ["boolean", "null"]},
        "excluded_cuisines": {"type": "array", "items": {"type": "string"}},
        "excluded_keywords": {"type": "array", "items": {"type": "string"}},
        "preference_tags": {"type": "array", "items": {"type": "string"}},
        "dish_terms": {"type": "array", "items": {"type": "string"}},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "walking_only": {"type": "boolean"},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "intent_type",
        "context_action",
        "clarification_message",
        "clear_fields",
        "keywords",
        "cuisines",
        "districts",
        "ambience_tags",
        "amenity_tags",
        "occasion_tags",
        "weather_tags",
        "price_min",
        "price_max",
        "budget_label",
        "group_size",
        "open_now",
        "excluded_cuisines",
        "excluded_keywords",
        "preference_tags",
        "dish_terms",
        "conflicts",
        "walking_only",
        "notes",
    ],
}


def should_use_openai_intent_parser() -> bool:
    return bool(settings.OPENAI_INTENT_PARSER and settings.OPENAI_API_KEY)


def parse_intent_with_openai(
    query: str,
    previous_query: str | None = None,
    previous_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIIntentParserError("OPENAI_API_KEY is missing.")

    payload = {
        "task": "Extract Vietnamese restaurant recommendation intent into strict JSON.",
        "rules": [
            "Return JSON only.",
            "Do not recommend restaurants. Only parse the user's intent.",
            "Keep unknown fields empty or null. Do not guess unsupported details.",
            "Use district slugs like quan-1, quan-3, quan-binh-thanh, tp-thu-duc.",
            "Use canonical cuisine labels: cà phê / brunch, lẩu, bbq / nướng, món nhật, món hàn, hải sản, chay / healthy, món thái, món ý, món việt.",
            "Use canonical ambience/amenity tags like yen_tinh, hen_ho, lam_viec, view_dep, o_cam, wifi, do_xe, nhom_dong, troi_mua.",
            "Choose context_action=fresh_search for a standalone new request.",
            "Choose context_action=refine_previous when the user is refining prior results like cheaper, nearer, another district, or another option.",
            "Choose context_action=switch_topic when the user changes craving/topic such as doi y, khong ... nua, them sushi, or wants a different cuisine/dish.",
            "When switching topic, use clear_fields to remove outdated fields from previous context such as cuisines, dish_terms, ambience_tags, amenity_tags, occasion_tags, weather_tags, and temporary preference_tags.",
            "When refining previous results, only set the fields the user is changing or adding; leave unrelated fields empty and do not clear them.",
            "Choose intent_type=out_of_domain when the message is mainly not about food, restaurants, booking, favorites, reviews, or eating context.",
            "Choose intent_type=unclear when the message is too short, meaningless, or lacks enough eating/restaurant context.",
            "For unclear or out_of_domain, set clarification_message to a concise Vietnamese user-facing reply that gently redirects to restaurant/food needs.",
            "For valid food/restaurant prompts, set clarification_message=null.",
            "For contradictory constraints, keep intent_type as restaurant_search and add concise Vietnamese conflict notes instead of rejecting the prompt.",
        ],
        "query": query,
        "previous_query": previous_query,
        "previous_intent": previous_intent,
        "schema": {
            "intent_type": "restaurant_search|restaurant_followup|booking_or_agent|preference_update|unclear|out_of_domain",
            "context_action": "fresh_search|refine_previous|switch_topic",
            "clarification_message": "string|null",
            "clear_fields": ["string"],
            "keywords": ["string"],
            "cuisines": ["string"],
            "districts": ["string"],
            "ambience_tags": ["string"],
            "amenity_tags": ["string"],
            "occasion_tags": ["string"],
            "weather_tags": ["string"],
            "price_min": "number|null",
            "price_max": "number|null",
            "budget_label": "binh_dan|trung_binh|kha_cao|cao_cap|null",
            "group_size": "number|null",
            "open_now": "boolean|null",
            "excluded_cuisines": ["string"],
            "excluded_keywords": ["string"],
            "preference_tags": ["string"],
            "dish_terms": ["string"],
            "conflicts": ["string"],
            "walking_only": "boolean",
            "notes": ["string"],
        },
    }
    try:
        parsed = request_structured_json(
            schema_name="restaurant_intent",
            schema=INTENT_SCHEMA,
            payload=payload,
            instructions="Parse restaurant search prompts into the requested structured JSON. Do not recommend restaurants.",
        )
    except OpenAIResponsesError as exc:
        raise OpenAIIntentParserError(str(exc)) from exc
    return _normalize_payload(parsed, query)


def _normalize_payload(payload: dict[str, Any], query: str) -> dict[str, Any]:
    return {
        "original_query": query,
        "normalized_query": normalize_text(query),
        "intent_type": payload.get("intent_type") if payload.get("intent_type") in ALLOWED_INTENT_TYPES else "restaurant_search",
        "context_action": payload.get("context_action") if payload.get("context_action") in ALLOWED_CONTEXT_ACTIONS else "fresh_search",
        "clarification_message": _optional_string(payload.get("clarification_message")),
        "clear_fields": _clear_fields(payload.get("clear_fields")),
        "keywords": _string_list(payload.get("keywords")) or tokenize(query),
        "cuisines": _canonical_string_list(payload.get("cuisines"), _canonical_map(CUISINE_PATTERNS)),
        "districts": _string_list(payload.get("districts")),
        "ambience_tags": _canonical_string_list(payload.get("ambience_tags"), _canonical_map(AMBIENCE_PATTERNS)),
        "amenity_tags": _canonical_string_list(payload.get("amenity_tags"), _canonical_map(AMENITY_PATTERNS)),
        "occasion_tags": _canonical_string_list(payload.get("occasion_tags"), _canonical_map(OCCASION_PATTERNS)),
        "weather_tags": _canonical_string_list(payload.get("weather_tags"), _canonical_map(WEATHER_PATTERNS)),
        "price_min": _optional_int(payload.get("price_min")),
        "price_max": _optional_int(payload.get("price_max")),
        "budget_label": payload.get("budget_label") if payload.get("budget_label") in ALLOWED_BUDGET_LABELS else None,
        "group_size": _optional_int(payload.get("group_size")),
        "open_now": payload.get("open_now") if isinstance(payload.get("open_now"), bool) else None,
        "excluded_cuisines": _canonical_string_list(payload.get("excluded_cuisines"), _canonical_map(CUISINE_PATTERNS)),
        "excluded_keywords": _string_list(payload.get("excluded_keywords")),
        "preference_tags": _canonical_string_list(payload.get("preference_tags"), _canonical_map(PREFERENCE_PATTERNS)),
        "dish_terms": _canonical_string_list(payload.get("dish_terms"), _canonical_map(DISH_PATTERNS), preserve_unknown=True),
        "conflicts": _string_list(payload.get("conflicts")),
        "walking_only": bool(payload.get("walking_only")),
        "parser_mode": "openai",
        "notes": _string_list(payload.get("notes")),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _optional_string(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _canonical_map(patterns_map: dict[str, list[str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for label, patterns in patterns_map.items():
        mapping[normalize_text(label)] = label
        for pattern in patterns:
            mapping[normalize_text(pattern)] = label
    return mapping


def _canonical_string_list(
    value: Any,
    mapping: dict[str, str],
    *,
    preserve_unknown: bool = False,
) -> list[str]:
    canonical_values: list[str] = []
    for item in _string_list(value):
        normalized_item = normalize_text(item)
        if normalized_item in mapping:
            canonical_values.append(mapping[normalized_item])
        elif preserve_unknown and normalized_item:
            canonical_values.append(item.strip())
    return unique_preserve_order(canonical_values)


def _clear_fields(value: Any) -> list[str]:
    return [field for field in _string_list(value) if field in ALLOWED_CLEAR_FIELDS]


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
