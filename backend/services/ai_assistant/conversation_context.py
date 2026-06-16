from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from models.ai_chat import AIChatMessage, AIChatSession, RecommendationLog
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommend_imports import normalize_text, parse_query_heuristically, unique_preserve_order


CONTEXT_CUES = {
    "gan hon",
    "re hon",
    "hon di",
    "hon nua",
    "duoi",
    "tren",
    "quan khac",
    "khac di",
    "them quan",
    "co quan nao",
    "gan toi",
    "xa hon",
    "con ban",
    "dung goi y",
    "toi an mon nay nhieu roi",
    "toi vua an com roi",
    "ghet an cay",
    "it pho bien hon",
    "danh sach vua roi",
    "vua roi",
    "xem thong tin",
}

REPEAT_AVOIDANCE_CUES = {
    "quan khac",
    "khac di",
    "doi quan",
    "them quan",
    "goi y khac",
    "dung goi y lai",
    "vua xem",
    "an mon nay nhieu roi",
    "it pho bien hon",
}


def get_conversation_context(db: Session, session_id: UUID | None, query: str, current_intent: Any) -> dict[str, Any]:
    if not session_id:
        return _empty_context()

    session = _get_session(db, session_id)
    previous_user_message = _get_previous_user_message(db, session_id)
    recent_user_queries = _get_recent_user_queries(db, session_id)
    recent_user_intents = _get_recent_user_intents(db, session_id)
    previous_result_ids = _get_previous_result_ids(db, session_id)
    normalized_query = normalize_text(query)

    return {
        "session": session,
        "previous_query": previous_user_message.content if previous_user_message else None,
        "previous_intent": _extract_message_intent(previous_user_message),
        "previous_result_ids": previous_result_ids,
        "recent_user_queries": recent_user_queries,
        "recent_user_intents": recent_user_intents,
        "use_previous_context": _should_use_previous_context(normalized_query, current_intent, previous_user_message),
        "avoid_repeated_results": any(cue in normalized_query for cue in REPEAT_AVOIDANCE_CUES),
        "context_summary": session.context_summary if session else None,
    }


def summarize_context(
    query: str,
    filters_applied: dict[str, Any] | None,
    result_restaurant_ids: list[str] | None,
    agent_state: str | None = None,
) -> str:
    filters_applied = filters_applied or {}
    result_restaurant_ids = result_restaurant_ids or []
    parts = [
        f"latest_query={query}",
        f"cuisines={','.join(filters_applied.get('cuisines') or [])}",
        f"districts={','.join(filters_applied.get('districts') or [])}",
        f"price_min={filters_applied.get('price_min')}",
        f"price_max={filters_applied.get('price_max')}",
        f"group_size={filters_applied.get('group_size')}",
        f"last_results={','.join(result_restaurant_ids[:5])}",
    ]
    if agent_state:
        parts.append(f"agent_state={agent_state}")
    return " | ".join(parts)


def _empty_context() -> dict[str, Any]:
    return {
        "session": None,
        "previous_query": None,
        "previous_intent": None,
        "previous_result_ids": [],
        "recent_user_queries": [],
        "recent_user_intents": [],
        "use_previous_context": False,
        "avoid_repeated_results": False,
        "context_summary": None,
    }


def _get_session(db: Session, session_id: UUID) -> AIChatSession | None:
    try:
        return (
            db.query(AIChatSession)
            .filter(AIChatSession.session_id == session_id)
            .first()
        )
    except Exception:
        return None


def _get_previous_user_message(db: Session, session_id: UUID) -> AIChatMessage | None:
    try:
        return (
            db.query(AIChatMessage)
            .filter(AIChatMessage.session_id == session_id, AIChatMessage.role == "user")
            .order_by(AIChatMessage.created_at.desc())
            .first()
        )
    except Exception:
        return None


def _extract_message_intent(message: AIChatMessage | None) -> dict[str, Any] | None:
    if not message:
        return None
    extracted_intent = getattr(message, "extracted_intent", None)
    return extracted_intent if isinstance(extracted_intent, dict) else None


def _get_previous_result_ids(db: Session, session_id: UUID) -> list[str]:
    try:
        logs = (
            db.query(RecommendationLog)
            .filter(RecommendationLog.session_id == session_id)
            .order_by(RecommendationLog.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception:
        return []

    ids: list[str] = []
    for log in logs:
        restaurant_id = str(log.restaurant_id)
        if restaurant_id not in ids:
            ids.append(restaurant_id)
    return ids


def _get_recent_user_queries(db: Session, session_id: UUID) -> list[str]:
    try:
        messages = (
            db.query(AIChatMessage)
            .filter(AIChatMessage.session_id == session_id, AIChatMessage.role == "user")
            .order_by(AIChatMessage.created_at.desc())
            .limit(8)
            .all()
        )
    except Exception:
        return []
    return [message.content for message in reversed(messages)]


def _get_recent_user_intents(db: Session, session_id: UUID) -> list[dict[str, Any]]:
    try:
        messages = (
            db.query(AIChatMessage)
            .filter(AIChatMessage.session_id == session_id, AIChatMessage.role == "user")
            .order_by(AIChatMessage.created_at.desc())
            .limit(8)
            .all()
        )
    except Exception:
        return []
    intents: list[dict[str, Any]] = []
    for message in reversed(messages):
        if isinstance(message.extracted_intent, dict):
            intents.append(message.extracted_intent)
    return intents


def apply_conversation_memory(
    intent: Any,
    recent_user_queries: list[str],
    recent_user_intents: list[dict[str, Any]] | None = None,
) -> Any:
    if not recent_user_queries and not recent_user_intents:
        return intent

    recent_user_intents = recent_user_intents or []
    stable_preference_tags = {
        "healthy",
        "vegetarian_option",
        "kid_friendly",
        "group_work",
        "outdoor_seating",
        "parking",
        "quick_service",
        "less_popular",
    }

    for index, query in enumerate(recent_user_queries):
        memory_intent = recent_user_intents[index] if index < len(recent_user_intents) else parse_query_heuristically(query).to_dict()
        for key in ("excluded_cuisines", "excluded_keywords"):
            previous_values = intent_value(intent, key, []) or []
            memory_values = intent_value(memory_intent, key, []) or []
            _set_intent_value(intent, key, unique_preserve_order([*previous_values, *memory_values]))
        if _is_profile_like_query(query, memory_intent):
            previous_preferences = intent_value(intent, "preference_tags", []) or []
            memory_preferences = [
                tag
                for tag in (intent_value(memory_intent, "preference_tags", []) or [])
                if tag in stable_preference_tags
            ]
            if memory_preferences:
                _set_intent_value(
                    intent,
                    "preference_tags",
                    unique_preserve_order([*previous_preferences, *memory_preferences]),
                )
    return intent


def _set_intent_value(intent: Any, key: str, value: Any) -> None:
    if isinstance(intent, dict):
        intent[key] = value
    else:
        setattr(intent, key, value)


def _is_profile_like_query(query: str, memory_intent: dict[str, Any]) -> bool:
    normalized = normalize_text(query)
    profile_cues = {
        "toi ghet",
        "toi khong an",
        "khong thich",
        "toi thich",
        "hay an",
        "thuong an",
        "dua tren so thich",
        "theo so thich",
    }
    if any(cue in normalized for cue in profile_cues):
        return True
    preference_tags = set(intent_value(memory_intent, "preference_tags", []) or [])
    return bool(
        preference_tags
        & {
            "healthy",
            "vegetarian_option",
            "kid_friendly",
            "group_work",
            "outdoor_seating",
            "parking",
            "quick_service",
            "less_popular",
        }
    )


def _should_use_previous_context(normalized_query: str, current_intent: Any, previous_user_message: AIChatMessage | None) -> bool:
    if not previous_user_message:
        return False
    if any(cue in normalized_query for cue in CONTEXT_CUES):
        return True

    strong_fields = [
        intent_value(current_intent, "cuisines", []) or [],
        intent_value(current_intent, "districts", []) or [],
        intent_value(current_intent, "ambience_tags", []) or [],
        intent_value(current_intent, "amenity_tags", []) or [],
        intent_value(current_intent, "occasion_tags", []) or [],
        intent_value(current_intent, "weather_tags", []) or [],
    ]
    has_structured_intent = any(strong_fields) or any(
        intent_value(current_intent, key) is not None
        for key in ("price_min", "price_max", "budget_label", "group_size", "open_now")
    )
    keywords = intent_value(current_intent, "keywords", []) or []
    return not has_structured_intent and len(keywords) <= 3
