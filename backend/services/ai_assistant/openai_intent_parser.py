from __future__ import annotations

from typing import Any

from core.config import settings
from services.ai_assistant.openai_response_client import OpenAIResponsesError, request_structured_json
from services.ai_assistant.recommend_imports import normalize_text, tokenize


class OpenAIIntentParserError(RuntimeError):
    pass


ALLOWED_BUDGET_LABELS = {"binh_dan", "trung_binh", "kha_cao", "cao_cap"}
INTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
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


def parse_intent_with_openai(query: str, previous_query: str | None = None) -> dict[str, Any]:
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
        ],
        "query": query,
        "previous_query": previous_query,
        "schema": {
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
        "keywords": _string_list(payload.get("keywords")) or tokenize(query),
        "cuisines": _string_list(payload.get("cuisines")),
        "districts": _string_list(payload.get("districts")),
        "ambience_tags": _string_list(payload.get("ambience_tags")),
        "amenity_tags": _string_list(payload.get("amenity_tags")),
        "occasion_tags": _string_list(payload.get("occasion_tags")),
        "weather_tags": _string_list(payload.get("weather_tags")),
        "price_min": _optional_int(payload.get("price_min")),
        "price_max": _optional_int(payload.get("price_max")),
        "budget_label": payload.get("budget_label") if payload.get("budget_label") in ALLOWED_BUDGET_LABELS else None,
        "group_size": _optional_int(payload.get("group_size")),
        "open_now": payload.get("open_now") if isinstance(payload.get("open_now"), bool) else None,
        "excluded_cuisines": _string_list(payload.get("excluded_cuisines")),
        "excluded_keywords": _string_list(payload.get("excluded_keywords")),
        "preference_tags": _string_list(payload.get("preference_tags")),
        "dish_terms": _string_list(payload.get("dish_terms")),
        "conflicts": _string_list(payload.get("conflicts")),
        "walking_only": bool(payload.get("walking_only")),
        "parser_mode": "openai",
        "notes": _string_list(payload.get("notes")),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
