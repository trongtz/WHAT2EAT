from __future__ import annotations

import json
import re
from typing import Any

from core.config import settings
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.openai_response_client import OpenAIResponsesError, request_structured_json
from services.ai_assistant.recommend_imports import normalize_text, parse_query_heuristically


MODE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "mode": {
            "type": "string",
            "enum": [
                "new_search",
                "follow_up_search",
                "restaurant_focus",
                "booking_flow",
                "profile_preference",
                "small_talk",
                "unknown",
            ],
        },
        "reason": {"type": ["string", "null"]},
    },
    "required": ["mode", "reason"],
}

MODE_FRESH_SEARCH_CUES = {
    "toi muon an",
    "muon an",
    "tim mon",
    "goi y mon",
    "goi y quan",
    "tim quan",
    "mon khac",
    "tiep tuc tim",
    "doi mon",
    "an gi",
}
MODE_FOLLOW_UP_CUES = {
    "gan hon",
    "re hon",
    "duoi",
    "tren",
    "them quan",
    "co quan nao",
    "xa hon",
    "dung goi y",
    "it pho bien hon",
    "khac nua",
    "danh sach vua roi",
    "vua roi",
}
MODE_RESTAURANT_CUES = {
    "quan nay",
    "quan do",
    "thong tin quan",
    "xem thong tin",
    "xem review",
    "review quan",
    "luu quan",
    "yeu thich",
    "bo yeu thich",
    "checkin",
    "check in",
    "xem quan",
    "chon quan",
}
MODE_BOOKING_CUES = {
    "dat ban",
    "dat cho",
    "booking",
    "reservation",
    "con cho",
    "con ban",
    "co ban trong",
    "ok dat",
    "xac nhan",
    "huy dat",
    "doi sang",
    "chuyen sang",
}
MODE_PREFERENCE_CUES = {
    "toi ghet",
    "toi khong an",
    "khong thich",
    "toi thich",
    "hay an",
    "thuong an",
}
MODE_SMALL_TALK_CUES = {
    "xin chao",
    "chao",
    "hello",
    "hi",
    "cam on",
    "ok",
    "oke",
}
AGENT_STATE_PREFIX = "agent_state="


class OpenAIModeClassifierError(RuntimeError):
    pass


def should_use_openai_mode_classifier() -> bool:
    return bool(settings.OPENAI_MODE_CLASSIFIER and settings.OPENAI_API_KEY)


def classify_conversation_mode(
    *,
    query: str,
    current_intent: Any,
    conversation_context: dict[str, Any],
) -> dict[str, Any]:
    normalized_query = normalize_text(query)
    agent_state = load_agent_state(conversation_context.get("context_summary"))
    heuristic_mode = _heuristic_mode(
        normalized_query=normalized_query,
        current_intent=current_intent,
        conversation_context=conversation_context,
        agent_state=agent_state,
    )
    if _should_skip_openai_mode_classifier(
        normalized_query=normalized_query,
        current_intent=current_intent,
        conversation_context=conversation_context,
        agent_state=agent_state,
        heuristic_mode=heuristic_mode,
    ):
        return heuristic_mode
    if should_use_openai_mode_classifier():
        try:
            parsed = _classify_mode_with_openai(
                query=query,
                previous_query=conversation_context.get("previous_query"),
                current_intent=current_intent,
                latest_result_count=len(conversation_context.get("previous_result_ids") or []),
                agent_state=agent_state,
                heuristic_mode=heuristic_mode["mode"],
            )
            return _guard_mode_selection(
                parsed,
                heuristic_mode=heuristic_mode,
                normalized_query=normalized_query,
                current_intent=current_intent,
                agent_state=agent_state,
            )
        except OpenAIModeClassifierError:
            pass
    return heuristic_mode


def load_agent_state(context_summary: str | None) -> dict[str, Any]:
    if not context_summary or AGENT_STATE_PREFIX not in context_summary:
        return {}
    raw = context_summary.split(AGENT_STATE_PREFIX, 1)[1].strip()
    if " | " in raw:
        raw = raw.split(" | ", 1)[0].strip()
    try:
        state = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return state if isinstance(state, dict) else {}


def _classify_mode_with_openai(
    *,
    query: str,
    previous_query: str | None,
    current_intent: Any,
    latest_result_count: int,
    agent_state: dict[str, Any],
    heuristic_mode: str,
) -> dict[str, Any]:
    try:
        payload = {
            "task": "Classify the user's Vietnamese restaurant assistant message into one conversation mode.",
            "rules": [
                "Return JSON only.",
                "Use new_search when the user starts a fresh restaurant or dish search.",
                "Use follow_up_search when the user refines prior search results without locking a single restaurant.",
                "Use restaurant_focus when the user refers to a specific restaurant, review, favorite, or detail action.",
                "Use booking_flow when the user is booking, confirming, canceling, or changing booking details.",
                "Use profile_preference when the user states stable preferences or dislikes.",
                "Use small_talk only for greeting/thanks/chitchat with no restaurant task.",
            ],
            "query": query,
            "previous_query": previous_query,
            "current_intent": {
                "cuisines": intent_value(current_intent, "cuisines", []) or [],
                "dish_terms": intent_value(current_intent, "dish_terms", []) or [],
                "districts": intent_value(current_intent, "districts", []) or [],
                "price_min": intent_value(current_intent, "price_min"),
                "price_max": intent_value(current_intent, "price_max"),
                "preference_tags": intent_value(current_intent, "preference_tags", []) or [],
            },
            "latest_result_count": latest_result_count,
            "agent_state": agent_state,
            "heuristic_mode": heuristic_mode,
        }
        parsed = request_structured_json(
            schema_name="conversation_mode",
            schema=MODE_SCHEMA,
            payload=payload,
            instructions="Classify the user message into one safe conversation mode for a restaurant assistant.",
        )
    except OpenAIResponsesError as exc:
        raise OpenAIModeClassifierError(str(exc)) from exc
    mode = str(parsed.get("mode") or "unknown")
    if mode not in {item for item in MODE_SCHEMA["properties"]["mode"]["enum"]}:
        mode = "unknown"
    return {
        "mode": mode,
        "reason": str(parsed.get("reason") or "").strip() or None,
        "source": "openai",
    }


def _heuristic_mode(
    *,
    normalized_query: str,
    current_intent: Any,
    conversation_context: dict[str, Any],
    agent_state: dict[str, Any],
) -> dict[str, Any]:
    pending_action = str(agent_state.get("pending_action") or "")
    has_previous_results = bool(conversation_context.get("previous_result_ids"))
    has_previous_query = bool(conversation_context.get("previous_query"))
    if pending_action and _looks_like_new_search(normalized_query, current_intent):
        return {"mode": "new_search", "reason": "Fresh search intent overrides pending flow.", "source": "heuristic"}
    if pending_action and _looks_like_booking_followup(normalized_query):
        return {"mode": "booking_flow", "reason": "Pending booking flow with booking follow-up.", "source": "heuristic"}
    if _looks_like_profile_preference(normalized_query):
        return {"mode": "profile_preference", "reason": "Stable preference statement.", "source": "heuristic"}
    if _looks_like_rich_fresh_search(
        normalized_query=normalized_query,
        current_intent=current_intent,
        has_previous_query=has_previous_query,
        has_previous_results=has_previous_results,
        agent_state=agent_state,
    ):
        return {"mode": "new_search", "reason": "Rich standalone search request.", "source": "heuristic"}
    if _looks_like_booking_followup(normalized_query):
        return {"mode": "booking_flow", "reason": "Booking or availability request.", "source": "heuristic"}
    if _looks_like_restaurant_focus(normalized_query):
        return {"mode": "restaurant_focus", "reason": "Specific restaurant follow-up.", "source": "heuristic"}
    if has_previous_results and _looks_like_follow_up_search(normalized_query):
        return {"mode": "follow_up_search", "reason": "Refinement of previous search results.", "source": "heuristic"}
    if _looks_like_new_search(normalized_query, current_intent):
        return {"mode": "new_search", "reason": "Fresh restaurant search request.", "source": "heuristic"}
    if _looks_like_small_talk(normalized_query):
        return {"mode": "small_talk", "reason": "Greeting or small talk.", "source": "heuristic"}
    if has_previous_query and len((intent_value(current_intent, "keywords", []) or [])) <= 3:
        return {"mode": "follow_up_search", "reason": "Short contextual follow-up.", "source": "heuristic"}
    return {"mode": "new_search", "reason": "Default to fresh search.", "source": "heuristic"}


def _should_skip_openai_mode_classifier(
    *,
    normalized_query: str,
    current_intent: Any,
    conversation_context: dict[str, Any],
    agent_state: dict[str, Any],
    heuristic_mode: dict[str, Any],
) -> bool:
    mode = heuristic_mode.get("mode")
    if mode == "small_talk":
        return True
    if mode == "new_search" and _looks_like_rich_fresh_search(
        normalized_query=normalized_query,
        current_intent=current_intent,
        has_previous_query=bool(conversation_context.get("previous_query")),
        has_previous_results=bool(conversation_context.get("previous_result_ids")),
        agent_state=agent_state,
    ):
        return True
    return False


def _looks_like_rich_fresh_search(
    *,
    normalized_query: str,
    current_intent: Any,
    has_previous_query: bool,
    has_previous_results: bool,
    agent_state: dict[str, Any],
) -> bool:
    if has_previous_query or has_previous_results or agent_state.get("pending_action"):
        return False
    if _looks_like_follow_up_search(normalized_query) or _looks_like_restaurant_focus(normalized_query):
        return False

    strong_signal_count = 0
    for key in (
        "cuisines",
        "dish_terms",
        "districts",
        "ambience_tags",
        "amenity_tags",
        "occasion_tags",
        "weather_tags",
    ):
        if intent_value(current_intent, key, []) or []:
            strong_signal_count += 1
    for key in ("price_min", "price_max", "budget_label", "group_size", "open_now"):
        if intent_value(current_intent, key) is not None:
            strong_signal_count += 1
    if _looks_like_new_search(normalized_query, current_intent):
        strong_signal_count += 1
    return strong_signal_count >= 3


def _guard_mode_selection(
    openai_mode: dict[str, Any],
    *,
    heuristic_mode: dict[str, Any],
    normalized_query: str,
    current_intent: Any,
    agent_state: dict[str, Any],
) -> dict[str, Any]:
    if agent_state.get("pending_action") and _looks_like_new_search(normalized_query, current_intent):
        return {"mode": "new_search", "reason": "Guardrail: fresh search while pending flow.", "source": "guardrail"}
    if openai_mode["mode"] == "unknown":
        return heuristic_mode
    if heuristic_mode["mode"] == "restaurant_focus" and openai_mode["mode"] != "restaurant_focus":
        return heuristic_mode
    if heuristic_mode["mode"] in {"follow_up_search", "restaurant_focus"} and openai_mode["mode"] == "new_search":
        return heuristic_mode
    if heuristic_mode["mode"] == "new_search" and openai_mode["mode"] == "follow_up_search":
        return heuristic_mode
    if heuristic_mode["mode"] == "new_search" and openai_mode["mode"] in {"booking_flow", "restaurant_focus"}:
        if not _looks_like_booking_followup(normalized_query) and not _looks_like_restaurant_focus(normalized_query):
            return heuristic_mode
    return openai_mode


def _looks_like_new_search(normalized_query: str, current_intent: Any) -> bool:
    if _looks_like_follow_up_search(normalized_query) or _looks_like_restaurant_focus(normalized_query):
        return False
    heuristic_intent = parse_query_heuristically(normalized_query)
    if any(
        [
            heuristic_intent.cuisines,
            heuristic_intent.dish_terms,
            heuristic_intent.districts,
            heuristic_intent.ambience_tags,
            heuristic_intent.amenity_tags,
            heuristic_intent.occasion_tags,
            heuristic_intent.weather_tags,
            heuristic_intent.price_min is not None,
            heuristic_intent.price_max is not None,
            heuristic_intent.budget_label,
        ]
    ):
        return True
    if any(cue in normalized_query for cue in MODE_FRESH_SEARCH_CUES):
        return True
    return bool(intent_value(current_intent, "cuisines", []) or intent_value(current_intent, "dish_terms", []) or [])


def _looks_like_follow_up_search(normalized_query: str) -> bool:
    return any(cue in normalized_query for cue in MODE_FOLLOW_UP_CUES)


def _looks_like_restaurant_focus(normalized_query: str) -> bool:
    if _parse_restaurant_index(normalized_query) is not None:
        return True
    return any(cue in normalized_query for cue in MODE_RESTAURANT_CUES)


def _looks_like_booking_followup(normalized_query: str) -> bool:
    if re.search(r"\b\d{1,2}\s*(?:nguoi|khach|cho)\b", normalized_query):
        return True
    if re.search(r"\b\d{1,2}(?::|h)\d{0,2}\b", normalized_query):
        return True
    return any(cue in normalized_query for cue in MODE_BOOKING_CUES)


def _looks_like_profile_preference(normalized_query: str) -> bool:
    return any(cue in normalized_query for cue in MODE_PREFERENCE_CUES)


def _looks_like_small_talk(normalized_query: str) -> bool:
    return normalized_query in MODE_SMALL_TALK_CUES or any(
        normalized_query.startswith(cue + " ") for cue in MODE_SMALL_TALK_CUES
    )


def _parse_restaurant_index(normalized_query: str) -> int | None:
    patterns = [
        r"quan\s+(?:thu|so)\s*(\d+)",
        r"(?:xem|chon|dat|doi sang|chuyen sang)\s+quan\s+(\d+)",
        r"\bso\s*(\d+)\b",
        r"#\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized_query)
        if match:
            return int(match.group(1))
    return None
