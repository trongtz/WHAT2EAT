from __future__ import annotations

from typing import Any

from core.config import settings
from services.ai_assistant.openai_response_client import OpenAIResponsesError, request_structured_json


class OpenAIAgentPlannerError(RuntimeError):
    pass


AGENT_ACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "recommend",
                "select_restaurant",
                "get_restaurant_detail",
                "check_availability",
                "create_booking",
                "modify_pending_booking",
                "cancel_pending_booking",
                "modify_existing_booking",
                "cancel_existing_booking",
                "change_restaurant",
                "favorite_restaurant",
                "unfavorite_restaurant",
                "show_reviews",
                "create_review",
                "update_review",
                "delete_review",
                "ask_review_info",
                "ask_clarification",
                "save_preference",
                "none",
            ],
        },
        "restaurant_ref": {"type": ["string", "null"]},
        "restaurant_rank": {"type": ["integer", "null"]},
        "restaurant_id": {"type": ["string", "null"]},
        "booking_id": {"type": ["string", "null"]},
        "review_id": {"type": ["string", "null"]},
        "guest_count": {"type": ["integer", "null"]},
        "reservation_time_text": {"type": ["string", "null"]},
        "confirmation": {"type": "boolean"},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
        "preference_note": {"type": ["string", "null"]},
        "rating": {"type": ["integer", "null"]},
        "review_comment": {"type": ["string", "null"]},
        "user_visible_message": {"type": ["string", "null"]},
    },
    "required": [
        "action",
        "restaurant_ref",
        "restaurant_rank",
        "restaurant_id",
        "booking_id",
        "review_id",
        "guest_count",
        "reservation_time_text",
        "confirmation",
        "missing_fields",
        "preference_note",
        "rating",
        "review_comment",
        "user_visible_message",
    ],
}


def should_use_openai_agent_planner() -> bool:
    return bool(settings.OPENAI_AGENT_PLANNER and settings.OPENAI_API_KEY)


def plan_agent_action(
    *,
    query: str,
    agent_state: dict[str, Any],
    latest_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIAgentPlannerError("OPENAI_API_KEY is missing.")

    payload = {
        "task": "Plan one safe backend action for a Vietnamese restaurant assistant.",
        "rules": [
            "Return JSON only.",
            "Do not recommend or invent restaurants.",
            "Use restaurant_rank only when the user refers to a ranked previous result.",
            "Use create_booking only when the user clearly confirms a pending booking.",
            "Use check_availability when the user asks to book and provides enough info.",
            "Use modify_existing_booking when the user wants to change time or guest count of an existing booking.",
            "Use cancel_existing_booking when the user wants to cancel an existing booking.",
            "Use ask_clarification when booking info is missing.",
            "Use favorite_restaurant or unfavorite_restaurant for saving/removing a restaurant from favorites.",
            "Use show_reviews when the user asks to see reviews.",
            "Use create_review only when the user gives a rating or review content for a selected restaurant.",
            "Use update_review when the user asks to edit their own existing review.",
            "Use delete_review when the user asks to remove their own existing review.",
            "Use ask_review_info when the user wants to review but rating/content is missing.",
            "Never bypass backend validation or confirmation.",
        ],
        "query": query,
        "agent_state": agent_state,
        "latest_results": latest_results[:5],
    }
    try:
        parsed = request_structured_json(
            schema_name="restaurant_agent_action",
            schema=AGENT_ACTION_SCHEMA,
            payload=payload,
            instructions=(
                "You are an action planner for WHAT2EAT. "
                "Choose exactly one backend action. The backend will execute tools and validate data."
            ),
        )
    except OpenAIResponsesError as exc:
        raise OpenAIAgentPlannerError(str(exc)) from exc
    return _normalize_action(parsed)


def _normalize_action(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "none")
    if action not in set(AGENT_ACTION_SCHEMA["properties"]["action"]["enum"]):
        action = "none"
    return {
        "action": action,
        "restaurant_ref": _optional_string(payload.get("restaurant_ref")),
        "restaurant_rank": _optional_int(payload.get("restaurant_rank")),
        "restaurant_id": _optional_string(payload.get("restaurant_id")),
        "booking_id": _optional_string(payload.get("booking_id")),
        "review_id": _optional_string(payload.get("review_id")),
        "guest_count": _optional_int(payload.get("guest_count")),
        "reservation_time_text": _optional_string(payload.get("reservation_time_text")),
        "confirmation": bool(payload.get("confirmation")),
        "missing_fields": _string_list(payload.get("missing_fields")),
        "preference_note": _optional_string(payload.get("preference_note")),
        "rating": _optional_int(payload.get("rating")),
        "review_comment": _optional_string(payload.get("review_comment")),
        "user_visible_message": _optional_string(payload.get("user_visible_message")),
        "planner_mode": "openai",
    }


def _optional_string(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]
