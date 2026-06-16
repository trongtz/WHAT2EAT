from __future__ import annotations

import re
from typing import Any

from services.ai_assistant.openai_intent_parser import (
    OpenAIIntentParserError,
    parse_intent_with_openai,
    should_use_openai_intent_parser,
)
from services.ai_assistant.recommend_imports import normalize_text, parse_query_heuristically, tokenize, unique_preserve_order


MERGEABLE_LIST_KEYS = {
    "keywords",
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
    "notes",
}
TOPIC_SWITCH_CLEAR_FIELDS = {
    "keywords",
    "cuisines",
    "ambience_tags",
    "amenity_tags",
    "occasion_tags",
    "weather_tags",
    "preference_tags",
    "dish_terms",
}


def extract_intent(
    query: str,
    previous_query: str | None = None,
    previous_intent: Any = None,
) -> Any:
    intent: Any
    local_intent = parse_query_heuristically(query) if parse_query_heuristically else _fallback_intent(query)
    previous_context_intent = previous_intent
    if previous_context_intent is None and previous_query:
        previous_context_intent = parse_query_heuristically(previous_query) if parse_query_heuristically else _fallback_intent(previous_query)
    if should_use_openai_intent_parser():
        try:
            parsed_intent = parse_intent_with_openai(
                query,
                previous_query=previous_query,
                previous_intent=intent_to_dict(previous_context_intent) if previous_context_intent else None,
            )
            intent = _merge_local_heuristics(parsed_intent, local_intent)
            if previous_query and not _has_explicit_cuisine_marker(local_intent) and not (intent_value(local_intent, "dish_terms", []) or []):
                intent["cuisines"] = []
            if previous_context_intent:
                intent = _merge_intent_like(previous_context_intent, intent)
            return _apply_general_intent_safeguards(intent)
        except OpenAIIntentParserError:
            pass

    intent = local_intent
    if isinstance(intent, dict):
        intent["context_action"] = _infer_context_action(query, local_intent, previous_context_intent)
        intent["clear_fields"] = _default_clear_fields_for_action(intent["context_action"], intent)
    else:
        intent.context_action = _infer_context_action(query, local_intent, previous_context_intent)
        intent.clear_fields = _default_clear_fields_for_action(intent.context_action, intent)

    if not previous_context_intent:
        return _apply_general_intent_safeguards(intent)

    return _apply_general_intent_safeguards(_merge_intent_like(previous_context_intent, intent))


def intent_value(intent: Any, key: str, default: Any = None) -> Any:
    if isinstance(intent, dict):
        return intent.get(key, default)
    return getattr(intent, key, default)


def intent_to_dict(intent: Any) -> dict[str, Any]:
    if hasattr(intent, "to_dict"):
        payload = intent.to_dict()
        for extra_key in ("context_action", "clear_fields"):
            if hasattr(intent, extra_key):
                payload[extra_key] = getattr(intent, extra_key)
        return payload
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
        "context_action": "fresh_search",
        "clear_fields": [],
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
    merged["context_action"] = str(merged.get("context_action") or "fresh_search")
    broad_recommendation = _is_broad_recommendation(local_intent)
    keep_only_dish_filter = _should_keep_only_dish_filter(local_intent)
    if broad_recommendation:
        # For vague prompts, GPT should help understand mood, not invent hard filters.
        merged["cuisines"] = []
        merged["dish_terms"] = []
    if keep_only_dish_filter:
        # If the user names a concrete dish but does not explicitly mention a cuisine,
        # keep the query dish-driven and avoid hard cuisine filters inferred from that dish.
        merged["cuisines"] = []
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
        local_values = intent_value(local_intent, key, []) or []
        if key == "cuisines" and keep_only_dish_filter:
            local_values = []
        if key == "dish_terms" and broad_recommendation:
            local_values = []
        merged[key] = unique_preserve_order(
            [
                *(merged.get(key) or []),
                *local_values,
            ]
        )
    for key in ("price_min", "price_max", "budget_label", "group_size", "open_now"):
        if merged.get(key) is None:
            merged[key] = intent_value(local_intent, key)
    merged["walking_only"] = bool(merged.get("walking_only") or intent_value(local_intent, "walking_only", False))
    if not merged.get("clear_fields"):
        merged["clear_fields"] = _default_clear_fields_for_action(merged["context_action"], merged)
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


def _should_prefer_local_dish_only(local_intent: Any) -> bool:
    local_cuisines = intent_value(local_intent, "cuisines", []) or []
    local_dish_terms = intent_value(local_intent, "dish_terms", []) or []
    if local_cuisines or not local_dish_terms:
        return False
    return not _has_explicit_cuisine_marker(local_intent)


def _should_keep_only_dish_filter(local_intent: Any) -> bool:
    local_dish_terms = intent_value(local_intent, "dish_terms", []) or []
    if not local_dish_terms:
        return False
    normalized_dishes = {normalize_text(dish) for dish in local_dish_terms}
    if normalized_dishes & {"ca phe", "tra sua"}:
        return False
    return not _has_explicit_cuisine_marker(local_intent)


def _has_explicit_cuisine_marker(local_intent: Any) -> bool:
    normalized = normalize_text(intent_value(local_intent, "original_query", ""))
    explicit_cuisine_markers = [
        "mon viet",
        "viet nam",
        "mon han",
        "han quoc",
        "korean",
        "mon nhat",
        "nhat ban",
        "japanese",
        "mon thai",
        "thai lan",
        "mon thai lan",
        "mon y",
        "italian",
        "mon trung hoa",
        "trung hoa",
        "chinese",
        "chay",
        "healthy",
        "vegan",
        "vegetarian",
        "hai san",
        "seafood",
        "bbq",
        "nuong",
        "lau",
        "buffet",
        "ca phe",
        "coffee",
        "brunch",
    ]
    return any(marker in normalized for marker in explicit_cuisine_markers)


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


def _infer_context_action(query: str, local_intent: Any, previous_intent: Any) -> str:
    if previous_intent is None:
        return "fresh_search"
    normalized = normalize_text(query)
    if _looks_like_topic_switch(normalized, local_intent, previous_intent):
        return "switch_topic"
    if _looks_like_refine_previous(normalized, local_intent):
        return "refine_previous"
    return "fresh_search"


def _looks_like_refine_previous(normalized_query: str, local_intent: Any) -> bool:
    refine_cues = {
        "re hon",
        "gan hon",
        "xa hon",
        "them quan",
        "co quan nao",
        "khac nua",
        "vua roi",
        "danh sach vua roi",
        "duoi",
        "tren",
        "tam",
        "gan binh thanh hon",
    }
    if any(cue in normalized_query for cue in refine_cues):
        return True
    has_core_topic = bool((intent_value(local_intent, "cuisines", []) or []) or (intent_value(local_intent, "dish_terms", []) or []))
    changed_scalar = any(intent_value(local_intent, key) is not None for key in ("price_min", "price_max", "group_size", "open_now"))
    changed_location = bool(intent_value(local_intent, "districts", []) or [])
    return not has_core_topic and (changed_scalar or changed_location)


def _looks_like_topic_switch(normalized_query: str, local_intent: Any, previous_intent: Any) -> bool:
    switch_cues = {
        "thoi doi y",
        "doi y roi",
        "khong an",
        "khong muon an",
        "khong an nua",
        "khong goi y",
        "doi mon",
        "mon khac",
        "thich sushi",
        "them sushi",
        "khac di",
    }
    if any(cue in normalized_query for cue in switch_cues):
        return True
    current_topics = {
        *(normalize_text(item) for item in (intent_value(local_intent, "cuisines", []) or [])),
        *(normalize_text(item) for item in (intent_value(local_intent, "dish_terms", []) or [])),
    }
    previous_topics = {
        *(normalize_text(item) for item in (intent_value(previous_intent, "cuisines", []) or [])),
        *(normalize_text(item) for item in (intent_value(previous_intent, "dish_terms", []) or [])),
    }
    if current_topics and previous_topics and current_topics.isdisjoint(previous_topics):
        return True
    return False


def _default_clear_fields_for_action(action: str, intent: Any) -> list[str]:
    if action != "switch_topic":
        return []
    clear_fields = set(TOPIC_SWITCH_CLEAR_FIELDS)
    if intent_value(intent, "excluded_cuisines", []) or intent_value(intent, "excluded_keywords", []) or intent_value(intent, "preference_tags", []):
        clear_fields.discard("preference_tags")
    return sorted(clear_fields)


def _apply_general_intent_safeguards(intent: Any) -> Any:
    normalized = normalize_text(intent_value(intent, "original_query", ""))
    if not _should_keep_only_dish_filter(intent):
        pass
    elif isinstance(intent, dict):
        intent["cuisines"] = []
    else:
        intent.cuisines = []
    if any(phrase in normalized for phrase in ["khong an mon nong", "khong an do nong", "khong muon an mon nong", "khong muon an do nong"]):
        current_preferences = intent_value(intent, "preference_tags", []) or []
        filtered_preferences = [tag for tag in current_preferences if tag != "hot_food"]
        current_excluded = intent_value(intent, "excluded_keywords", []) or []
        if isinstance(intent, dict):
            intent["preference_tags"] = filtered_preferences
            intent["excluded_keywords"] = unique_preserve_order([*current_excluded, "do nong"])
        else:
            intent.preference_tags = filtered_preferences
            intent.excluded_keywords = unique_preserve_order([*current_excluded, "do nong"])
    return intent


def _merge_intent_like(previous_intent: Any, current_intent: Any) -> Any:
    previous_dict = intent_to_dict(previous_intent)
    current_dict = intent_to_dict(current_intent)
    if not current_dict:
        return current_intent
    action = str(current_dict.get("context_action") or "refine_previous")
    clear_fields = set(current_dict.get("clear_fields") or [])
    if action == "fresh_search":
        merged: dict[str, Any] = {}
    else:
        merged = dict(previous_dict)
        if action == "switch_topic":
            for field in clear_fields or TOPIC_SWITCH_CLEAR_FIELDS:
                if field in MERGEABLE_LIST_KEYS:
                    merged[field] = []
                else:
                    merged[field] = None
    for key, value in current_dict.items():
        if key in MERGEABLE_LIST_KEYS:
            if value:
                merged[key] = unique_preserve_order([*(merged.get(key) or []), *value])
            else:
                merged[key] = merged.get(key) or []
            continue
        if value not in (None, "", []):
            merged[key] = value
        elif key not in merged:
            merged[key] = value
    merged["context_action"] = action
    merged["clear_fields"] = sorted(clear_fields)
    return merged


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
