from __future__ import annotations

import json
import re
from typing import Any

import httpx

from core.config import settings
from services.ai_assistant.recommend_imports import normalize_text, tokenize


class OpenAIIntentParserError(RuntimeError):
    pass


ALLOWED_BUDGET_LABELS = {"binh_dan", "trung_binh", "kha_cao", "cao_cap"}


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
            "notes": ["string"],
        },
    }
    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.OPENAI_MODEL,
                "input": [
                    {
                        "role": "system",
                        "content": "You parse restaurant search prompts. Return valid JSON only.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    },
                ],
            },
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise OpenAIIntentParserError("OpenAI request failed or timed out.") from exc

    if response.status_code >= 400:
        raise OpenAIIntentParserError(f"OpenAI request failed: {response.status_code}")

    return _normalize_payload(_extract_json(_extract_response_text(response.json())), query)


def _extract_response_text(response: dict[str, Any]) -> str:
    if response.get("output_text"):
        return str(response["output_text"])

    parts: list[str] = []
    for output_item in response.get("output", []) or []:
        for content_item in output_item.get("content", []) or []:
            text = content_item.get("text")
            if text:
                parts.append(str(text))
    if not parts:
        raise OpenAIIntentParserError("OpenAI response did not contain text.")
    return "\n".join(parts)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OpenAIIntentParserError("OpenAI response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise OpenAIIntentParserError("OpenAI response JSON was not an object.")
    return payload


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
