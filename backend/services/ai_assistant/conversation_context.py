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
    summary_intent = _intent_from_context_summary(session.context_summary if session else None)
    recent_user_queries = _get_recent_user_queries(db, session_id)
    recent_user_intents = _get_recent_user_intents(db, session_id)
    previous_result_ids = _get_previous_result_ids(db, session_id)
    normalized_query = normalize_text(query)

    return {
        "session": session,
        "previous_query": previous_user_message.content if previous_user_message else None,
        "previous_intent": _merge_summary_into_intent(_extract_message_intent(previous_user_message), summary_intent),
        "summary_intent": summary_intent,
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
        "summary_intent": None,
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
        db.rollback()
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
        db.rollback()
        return None


def _extract_message_intent(message: AIChatMessage | None) -> dict[str, Any] | None:
    if not message:
        return None
    extracted_intent = getattr(message, "extracted_intent", None)
    return extracted_intent if isinstance(extracted_intent, dict) else None


def _intent_from_context_summary(context_summary: str | None) -> dict[str, Any] | None:
    if not context_summary:
        return None

    fields: dict[str, str] = {}
    for part in context_summary.split(" | "):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()

    cuisines = [item for item in (fields.get("cuisines") or "").split(",") if item]
    districts = [item for item in (fields.get("districts") or "").split(",") if item]
    price_min = _parse_summary_int(fields.get("price_min"))
    price_max = _parse_summary_int(fields.get("price_max"))
    group_size = _parse_summary_int(fields.get("group_size"))

    if not any([cuisines, districts, price_min is not None, price_max is not None, group_size is not None]):
        return None

    return {
        "original_query": fields.get("latest_query") or "",
        "cuisines": cuisines,
        "districts": districts,
        "price_min": price_min,
        "price_max": price_max,
        "group_size": group_size,
        "keywords": [],
        "ambience_tags": [],
        "amenity_tags": [],
        "occasion_tags": [],
        "weather_tags": [],
        "excluded_cuisines": [],
        "excluded_keywords": [],
        "preference_tags": [],
        "dish_terms": [],
        "conflicts": [],
        "walking_only": False,
    }


def _merge_summary_into_intent(message_intent: dict[str, Any] | None, summary_intent: dict[str, Any] | None) -> dict[str, Any] | None:
    if not message_intent:
        return summary_intent
    if not summary_intent:
        return message_intent

    merged = dict(message_intent)
    for key in ("cuisines", "districts", "ambience_tags", "amenity_tags", "occasion_tags", "weather_tags", "dish_terms"):
        if not merged.get(key) and summary_intent.get(key):
            merged[key] = list(summary_intent[key])
    for key in ("price_min", "price_max", "group_size"):
        if merged.get(key) is None and summary_intent.get(key) is not None:
            merged[key] = summary_intent[key]
    return merged


def _parse_summary_int(value: str | None) -> int | None:
    if value in {None, "", "None"}:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _get_previous_result_ids(db: Session, session_id: UUID) -> list[str]:
    try:
        logs = (
            db.query(RecommendationLog)
            .filter(
                RecommendationLog.session_id == session_id,
                RecommendationLog.source != "AGENT",
            )
            .order_by(RecommendationLog.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception:
        db.rollback()
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
        db.rollback()
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
        db.rollback()
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


def reinforce_follow_up_context(
    intent: Any,
    conversation_context: dict[str, Any],
    *,
    mode_name: str,
) -> Any:
    if mode_name != "follow_up_search":
        return intent

    context_action = str(intent_value(intent, "context_action") or "")
    if context_action in {"fresh_search", "switch_topic"}:
        return intent

    memory_sources: list[dict[str, Any]] = []
    summary_intent = conversation_context.get("summary_intent")
    if isinstance(summary_intent, dict):
        memory_sources.append(summary_intent)

    recent_user_intents = conversation_context.get("recent_user_intents") or []
    for memory_intent in reversed(recent_user_intents[-4:]):
        if isinstance(memory_intent, dict):
            memory_sources.append(memory_intent)

    list_keys = (
        "cuisines",
        "districts",
        "ambience_tags",
        "amenity_tags",
        "occasion_tags",
        "weather_tags",
        "dish_terms",
    )
    scalar_keys = ("price_min", "price_max", "budget_label", "group_size", "open_now")

    for key in list_keys:
        current_values = intent_value(intent, key, []) or []
        if current_values:
            continue
        for memory_intent in memory_sources:
            memory_values = intent_value(memory_intent, key, []) or []
            if memory_values:
                _set_intent_value(intent, key, list(memory_values))
                break

    for key in scalar_keys:
        current_value = intent_value(intent, key)
        if current_value is not None:
            continue
        for memory_intent in memory_sources:
            memory_value = intent_value(memory_intent, key)
            if memory_value is not None:
                _set_intent_value(intent, key, memory_value)
                break

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

    local_intent = parse_query_heuristically(normalized_query)
    has_new_topic = bool(local_intent.cuisines or local_intent.dish_terms)
    has_refinement_fields = any(
        [
            local_intent.districts,
            local_intent.ambience_tags,
            local_intent.amenity_tags,
            local_intent.occasion_tags,
            local_intent.weather_tags,
            local_intent.price_min is not None,
            local_intent.price_max is not None,
            local_intent.budget_label,
            local_intent.group_size is not None,
            local_intent.open_now is not None,
            local_intent.walking_only,
        ]
    )
    if not has_new_topic and has_refinement_fields:
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
