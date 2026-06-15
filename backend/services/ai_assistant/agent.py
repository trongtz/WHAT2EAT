from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

import crud.reservation as crud_reservation
import crud.restaurant as crud_restaurant
from models.ai_chat import RecommendationLog
from models.restaurant import Restaurant
from models.user import User
from schemas.booking import ReservationCreate
from services.ai_assistant.openai_agent_planner import (
    OpenAIAgentPlannerError,
    plan_agent_action,
    should_use_openai_agent_planner,
)
from services.ai_assistant.recommend_imports import haversine_km, normalize_text
from services.capacity_service import get_restaurant_capacity_for_date


BOOKING_CUES = {
    "dat quan",
    "dat ban",
    "dat cho",
    "giu ban",
    "book ban",
    "booking",
    "reservation",
}
CONFIRM_CUES = {"ok", "oke", "okay", "dong y", "xac nhan", "chot", "dat di", "dat luon"}
DETAIL_CUES = {"quan thu", "quan so", "so ", "xem quan", "chon quan", "duoc do", "lay quan"}
CANCEL_CUES = {"huy", "thoi", "khong dat nua", "bo qua", "cancel"}
CHANGE_RESTAURANT_CUES = {"quan khac", "doi quan", "chon quan khac", "khac di"}
MODIFY_CUES = {"doi", "sua", "thay", "thanh", "luc", "gio", "nguoi", "khach", "cho"}
AGENT_STATE_PREFIX = "agent_state="


def handle_agent_turn(
    *,
    db: Session,
    query: str,
    current_user: User | None,
    session_id: UUID | None,
    conversation_context: dict[str, Any],
    latitude: float | None,
    longitude: float | None,
) -> dict[str, Any] | None:
    normalized_query = normalize_text(query)
    state = load_agent_state(conversation_context.get("context_summary"))
    latest_restaurants = _latest_recommended_restaurants(db, session_id)
    action = _resolve_agent_action(
        query=query,
        normalized_query=normalized_query,
        state=state,
        latest_restaurants=latest_restaurants,
    )

    if action["action"] == "cancel_pending_booking":
        return _cancel_pending_booking(action)

    if action["action"] == "change_restaurant":
        return _change_pending_restaurant(action)

    if _is_create_booking_action(action) and state.get("pending_action") == "confirm_booking":
        return _confirm_pending_booking(
            db=db,
            state=state,
            current_user=current_user,
            latitude=latitude,
            longitude=longitude,
        )

    if action["action"] == "save_preference":
        return _save_preference_note(state, action)

    is_booking = action["action"] in {"check_availability", "ask_clarification", "modify_pending_booking"}
    selected_restaurant = _resolve_restaurant_reference(
        db=db,
        query=query,
        normalized_query=normalized_query,
        session_id=session_id,
        state=state,
        action=action,
        latest_restaurants=latest_restaurants,
    )
    has_selection = selected_restaurant is not None and action["action"] in {
        "select_restaurant",
        "get_restaurant_detail",
    }

    if not is_booking and has_selection:
        return _build_selected_restaurant_response(
            selected_restaurant,
            latitude=latitude,
            longitude=longitude,
            action=action,
        )

    if not is_booking:
        return None

    guest_count = action.get("guest_count") or _coerce_int(state.get("guest_count"))
    reservation_time = (
        _parse_reservation_time(action.get("reservation_time_text") or "")
        or _parse_reservation_time(query)
        or _parse_iso_datetime(state.get("reservation_time"))
    )

    if selected_restaurant is None:
        return _build_agent_message(
            message=_build_missing_booking_message(None, ["quán"], guest_count, reservation_time),
            status="needs_restaurant",
            pending_state={
                "pending_action": "collect_booking_info",
                "guest_count": guest_count,
                "reservation_time": reservation_time.isoformat() if reservation_time else None,
            },
            action=action,
        )

    missing: list[str] = []
    if guest_count is None:
        missing.append("số người")
    if reservation_time is None:
        missing.append("thời gian")
    if missing:
        return _build_agent_message(
            message=_build_missing_booking_message(selected_restaurant, missing, guest_count, reservation_time),
            status="needs_booking_info",
            restaurant=selected_restaurant,
            latitude=latitude,
            longitude=longitude,
            pending_state={
                "pending_action": "collect_booking_info",
                "restaurant_id": str(selected_restaurant.restaurant_id),
                "restaurant_name": selected_restaurant.name,
                "guest_count": guest_count,
                "reservation_time": reservation_time.isoformat() if reservation_time else None,
            },
            action=action,
        )

    return _check_availability_and_ask_confirmation(
        db=db,
        restaurant=selected_restaurant,
        guest_count=guest_count,
        reservation_time=reservation_time,
        latitude=latitude,
        longitude=longitude,
        action=action,
    )


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


def serialize_agent_state(state: dict[str, Any] | None) -> str | None:
    if not state:
        return None
    clean_state = {key: value for key, value in state.items() if value is not None}
    if not clean_state:
        return None
    return json.dumps(clean_state, ensure_ascii=False, separators=(",", ":"))


def _cancel_pending_booking(action: dict[str, Any]) -> dict[str, Any]:
    return _build_agent_message(
        message="Mình đã hủy bước đặt bàn đang chờ. Bạn có thể yêu cầu gợi ý quán khác bất cứ lúc nào.",
        status="booking_cancelled",
        pending_state={},
        action=action,
    )


def _change_pending_restaurant(action: dict[str, Any]) -> dict[str, Any]:
    return _build_agent_message(
        message="Ok, mình bỏ lựa chọn quán hiện tại. Bạn nói nhu cầu mới hoặc chọn một quán khác trong danh sách gợi ý nhé.",
        status="needs_restaurant",
        pending_state={},
        action=action,
    )


def _resolve_agent_action(
    *,
    query: str,
    normalized_query: str,
    state: dict[str, Any],
    latest_restaurants: list[Restaurant],
) -> dict[str, Any]:
    if should_use_openai_agent_planner():
        try:
            return plan_agent_action(
                query=query,
                agent_state=state,
                latest_results=_latest_results_payload(latest_restaurants),
            )
        except OpenAIAgentPlannerError:
            pass
    return _rule_based_action(query, normalized_query, state)


def _rule_based_action(query: str, normalized_query: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = state or {}
    has_pending_booking = state.get("pending_action") in {"collect_booking_info", "confirm_booking"}
    if has_pending_booking and any(cue in normalized_query for cue in CANCEL_CUES):
        return _base_action(action="cancel_pending_booking", planner_mode="rule")
    if has_pending_booking and any(cue in normalized_query for cue in CHANGE_RESTAURANT_CUES):
        return _base_action(action="change_restaurant", planner_mode="rule")
    if has_pending_booking and (
        _parse_guest_count(normalized_query)
        or _parse_reservation_time(query)
        or _parse_restaurant_index(normalized_query)
        or any(cue in normalized_query for cue in MODIFY_CUES)
    ):
        return _base_action(
            action="modify_pending_booking",
            restaurant_rank=_parse_restaurant_index(normalized_query),
            guest_count=_parse_guest_count(normalized_query),
            reservation_time_text=query,
            planner_mode="rule",
        )
    if _is_confirmation(normalized_query):
        return _base_action(
            action="create_booking",
            confirmation=True,
            restaurant_rank=_parse_restaurant_index(normalized_query),
            guest_count=_parse_guest_count(normalized_query),
            reservation_time_text=query,
            planner_mode="rule",
        )
    if _is_booking_request(normalized_query):
        return _base_action(
            action="check_availability",
            restaurant_rank=_parse_restaurant_index(normalized_query),
            guest_count=_parse_guest_count(normalized_query),
            reservation_time_text=query,
            planner_mode="rule",
        )
    if _has_selection_cue(normalized_query):
        return _base_action(
            action="select_restaurant",
            restaurant_rank=_parse_restaurant_index(normalized_query),
            restaurant_ref=query,
            planner_mode="rule",
        )
    if any(cue in normalized_query for cue in ["toi ghet", "toi khong an", "khong thich"]):
        return _base_action(action="save_preference", preference_note=query, planner_mode="rule")
    return _base_action(action="none", planner_mode="rule")


def _base_action(**updates: Any) -> dict[str, Any]:
    action = {
        "action": "none",
        "restaurant_ref": None,
        "restaurant_rank": None,
        "restaurant_id": None,
        "guest_count": None,
        "reservation_time_text": None,
        "confirmation": False,
        "missing_fields": [],
        "preference_note": None,
        "user_visible_message": None,
        "planner_mode": "rule",
    }
    action.update(updates)
    return action


def _latest_results_payload(restaurants: list[Restaurant]) -> list[dict[str, Any]]:
    return [
        {
            "rank": index,
            "id": str(restaurant.restaurant_id),
            "name": restaurant.name,
            "address": restaurant.address,
            "price_range": restaurant.price_range,
        }
        for index, restaurant in enumerate(restaurants, start=1)
    ]


def _is_create_booking_action(action: dict[str, Any]) -> bool:
    return action.get("action") == "create_booking" or bool(action.get("confirmation"))


def _save_preference_note(state: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    note = action.get("preference_note") or "Ghi nhớ sở thích từ hội thoại."
    previous_notes = state.get("preference_notes") if isinstance(state.get("preference_notes"), list) else []
    preference_notes = [*previous_notes, note]
    pending_state = {
        **state,
        "pending_action": "preference_saved",
        "preference_notes": preference_notes[-10:],
    }
    return _build_agent_message(
        message=action.get("user_visible_message") or "Mình đã ghi nhớ sở thích này cho cuộc trò chuyện hiện tại.",
        status="preference_saved",
        pending_state=pending_state,
        action=action,
    )


def _build_missing_booking_message(
    restaurant: Restaurant | None,
    missing: list[str],
    guest_count: int | None,
    reservation_time: datetime | None,
) -> str:
    known_parts: list[str] = []
    if restaurant is not None:
        known_parts.append(f"quán {restaurant.name}")
    if guest_count is not None:
        known_parts.append(f"{guest_count} người")
    if reservation_time is not None:
        known_parts.append(f"lúc {_format_datetime(reservation_time)}")

    known_text = "Mình đã có " + ", ".join(known_parts) + ". " if known_parts else ""
    if missing == ["quán"]:
        return known_text + "Bạn muốn đặt quán nào trong danh sách vừa gợi ý? Ví dụ: “đặt quán thứ 2”."
    if missing == ["số người"]:
        return known_text + "Bạn đi mấy người để mình kiểm tra còn chỗ?"
    if missing == ["thời gian"]:
        return known_text + "Bạn muốn đặt lúc mấy giờ?"
    return known_text + "Bạn cho mình thêm " + " và ".join(missing) + " để kiểm tra còn chỗ nhé."


def _confirm_pending_booking(
    *,
    db: Session,
    state: dict[str, Any],
    current_user: User | None,
    latitude: float | None,
    longitude: float | None,
) -> dict[str, Any]:
    restaurant_id = _parse_uuid(state.get("restaurant_id"))
    reservation_time = _parse_iso_datetime(state.get("reservation_time"))
    guest_count = _coerce_int(state.get("guest_count"))
    restaurant = crud_restaurant.get_restaurant_by_id(db, restaurant_id) if restaurant_id else None

    if restaurant is None or reservation_time is None or guest_count is None:
        return _build_agent_message(
            message="Mình chưa có đủ thông tin đặt bàn. Bạn nói lại quán, số người và thời gian giúp mình nhé.",
            status="needs_booking_info",
            pending_state={},
        )
    if current_user is None:
        return _build_agent_message(
            message="Mình đã sẵn sàng đặt bàn, nhưng bạn cần đăng nhập tài khoản Customer trước khi tạo booking.",
            status="needs_login",
            restaurant=restaurant,
            latitude=latitude,
            longitude=longitude,
            pending_state=state,
        )

    validation_error = _validate_booking(db, restaurant, reservation_time, guest_count)
    if validation_error:
        return _build_agent_message(
            message=validation_error,
            status="booking_rejected",
            restaurant=restaurant,
            latitude=latitude,
            longitude=longitude,
            pending_state={},
            action=action,
        )

    reservation = crud_reservation.create_reservation(
        db,
        ReservationCreate(
            restaurant_id=restaurant.restaurant_id,
            reservation_time=reservation_time,
            guest_count=guest_count,
            notes="Created by WHAT2EAT AI agent",
        ),
        current_user.user_id,
    )
    return _build_agent_message(
        message=(
            f"Mình đã tạo yêu cầu đặt bàn tại {restaurant.name} cho {guest_count} người "
            f"lúc {_format_datetime(reservation_time)}. Mã booking: {reservation.reservation_id}."
        ),
        status="booking_created",
        restaurant=restaurant,
        latitude=latitude,
        longitude=longitude,
        booking={
            "reservation_id": str(reservation.reservation_id),
            "restaurant_id": str(reservation.restaurant_id),
            "reservation_time": reservation.reservation_time.isoformat(),
            "guest_count": reservation.guest_count,
            "status": reservation.status,
        },
        pending_state={},
    )


def _check_availability_and_ask_confirmation(
    *,
    db: Session,
    restaurant: Restaurant,
    guest_count: int,
    reservation_time: datetime,
    latitude: float | None,
    longitude: float | None,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation_error = _validate_booking(db, restaurant, reservation_time, guest_count)
    if validation_error:
        return _build_agent_message(
            message=validation_error,
            status="booking_rejected",
            restaurant=restaurant,
            latitude=latitude,
            longitude=longitude,
            pending_state={},
        )

    max_capacity = get_restaurant_capacity_for_date(db, restaurant.restaurant_id, reservation_time.date())
    available = crud_reservation.count_available_seats(db, restaurant.restaurant_id, reservation_time, max_capacity)
    return _build_agent_message(
        message=(
            f"{restaurant.name} còn khoảng {available} chỗ lúc {_format_datetime(reservation_time)} "
            f"cho nhóm {guest_count} người. Bạn xác nhận đặt bàn không?"
        ),
        status="awaiting_booking_confirmation",
        restaurant=restaurant,
        latitude=latitude,
        longitude=longitude,
        pending_state={
            "pending_action": "confirm_booking",
            "restaurant_id": str(restaurant.restaurant_id),
            "restaurant_name": restaurant.name,
            "guest_count": guest_count,
            "reservation_time": reservation_time.isoformat(),
            "available_capacity": available,
        },
        action=action,
    )


def _build_selected_restaurant_response(
    restaurant: Restaurant,
    *,
    latitude: float | None,
    longitude: float | None,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _build_agent_message(
        message=(
            f"Mình đã chọn {restaurant.name}. Quán ở {restaurant.address}. "
            "Nếu muốn đặt bàn, bạn nói kiểu “đặt quán này cho 4 người lúc 19h”."
        ),
        status="restaurant_selected",
        restaurant=restaurant,
        latitude=latitude,
        longitude=longitude,
        pending_state={
            "pending_action": "restaurant_selected",
            "restaurant_id": str(restaurant.restaurant_id),
            "restaurant_name": restaurant.name,
        },
        action=action,
    )


def _build_agent_message(
    *,
    message: str,
    status: str,
    restaurant: Restaurant | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    pending_state: dict[str, Any] | None = None,
    booking: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    restaurants = [_restaurant_payload(restaurant, latitude, longitude)] if restaurant is not None else []
    return {
        "message": message,
        "total_found": len(restaurants),
        "filters_applied": {},
        "result_restaurant_ids": [item["id"] for item in restaurants],
        "recommended_restaurants": restaurants,
        "source": "AGENT",
        "agent": {
            "enabled": True,
            "status": status,
            "action": action.get("action") if action else None,
            "planner_mode": action.get("planner_mode") if action else "rule",
            "pending_state": pending_state or {},
        },
        "agent_state": pending_state or {},
        "booking": booking,
    }


def _restaurant_payload(restaurant: Restaurant, latitude: float | None, longitude: float | None) -> dict[str, Any]:
    distance_km = haversine_km(
        latitude,
        longitude,
        float(restaurant.latitude) if restaurant.latitude is not None else None,
        float(restaurant.longitude) if restaurant.longitude is not None else None,
    )
    return {
        "id": str(restaurant.restaurant_id),
        "name": restaurant.name,
        "address": restaurant.address,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
        "match_score": None,
        "reason": "Được chọn từ kết quả gợi ý trước đó.",
        "available_capacity": None,
        "quality_score": None,
        "availability_score": None,
        "quality_signals": None,
    }


def _resolve_restaurant_reference(
    *,
    db: Session,
    query: str,
    normalized_query: str,
    session_id: UUID | None,
    state: dict[str, Any],
    action: dict[str, Any] | None = None,
    latest_restaurants: list[Restaurant] | None = None,
) -> Restaurant | None:
    action = action or {}
    latest_restaurants = latest_restaurants if latest_restaurants is not None else _latest_recommended_restaurants(db, session_id)
    action_restaurant_id = _parse_uuid(action.get("restaurant_id"))
    if action_restaurant_id:
        restaurant = crud_restaurant.get_restaurant_by_id(db, action_restaurant_id)
        if restaurant:
            return restaurant

    state_restaurant_id = _parse_uuid(state.get("restaurant_id"))
    if state_restaurant_id and action.get("action") in {
        "check_availability",
        "ask_clarification",
        "modify_pending_booking",
        "create_booking",
    }:
        restaurant = crud_restaurant.get_restaurant_by_id(db, state_restaurant_id)
        if restaurant:
            return restaurant
    if state_restaurant_id and any(cue in normalized_query for cue in ["quan nay", "quan do", "o do", "dat di", "dat luon"]):
        restaurant = crud_restaurant.get_restaurant_by_id(db, state_restaurant_id)
        if restaurant:
            return restaurant

    index = action.get("restaurant_rank") or _parse_restaurant_index(normalized_query)
    if index is not None and 0 <= index - 1 < len(latest_restaurants):
        return latest_restaurants[index - 1]

    normalized_query_text = normalize_text(action.get("restaurant_ref") or query)
    for restaurant in latest_restaurants:
        if normalize_text(restaurant.name) in normalized_query_text:
            return restaurant

    if _looks_like_restaurant_name(query):
        matches = crud_restaurant.search_restaurants(db, query=query, limit=1)
        return matches[0] if matches else None
    return None


def _latest_recommended_restaurants(db: Session, session_id: UUID | None) -> list[Restaurant]:
    if session_id is None:
        return []
    logs = (
        db.query(RecommendationLog)
        .filter(RecommendationLog.session_id == session_id)
        .order_by(RecommendationLog.created_at.desc())
        .limit(30)
        .all()
    )
    if not logs:
        return []
    latest_prompt = logs[0].prompt_summary
    grouped = [log for log in logs if log.prompt_summary == latest_prompt]
    grouped.sort(key=lambda log: log.rank_position or 999)
    restaurants: list[Restaurant] = []
    for log in grouped:
        restaurant = crud_restaurant.get_restaurant_by_id(db, log.restaurant_id)
        if restaurant:
            restaurants.append(restaurant)
    return restaurants


def _validate_booking(db: Session, restaurant: Restaurant, reservation_time: datetime, guest_count: int) -> str | None:
    if restaurant.status != "APPROVED" or not restaurant.is_active:
        return f"{restaurant.name} hiện chưa nhận đặt bàn qua hệ thống."
    minimum_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
    if reservation_time <= minimum_time:
        return "Thời gian đặt bàn cần cách hiện tại ít nhất 30 phút. Bạn chọn giờ khác giúp mình nhé."
    max_capacity = get_restaurant_capacity_for_date(db, restaurant.restaurant_id, reservation_time.date())
    if max_capacity <= 0:
        return f"{restaurant.name} chưa có thông tin sức chứa cho ngày này."
    if guest_count > max_capacity:
        return f"{restaurant.name} chỉ có tối đa {max_capacity} chỗ cho khung ngày này."
    if not crud_reservation.check_overbooking(db, restaurant.restaurant_id, reservation_time, guest_count, max_capacity):
        return f"{restaurant.name} không còn đủ {guest_count} chỗ vào {_format_datetime(reservation_time)}."
    return None


def _is_booking_request(normalized_query: str) -> bool:
    return any(cue in normalized_query for cue in BOOKING_CUES)


def _is_confirmation(normalized_query: str) -> bool:
    return any(re.search(rf"\b{re.escape(cue)}\b", normalized_query) for cue in CONFIRM_CUES)


def _has_selection_cue(normalized_query: str) -> bool:
    return any(cue in normalized_query for cue in DETAIL_CUES)


def _parse_restaurant_index(normalized_query: str) -> int | None:
    patterns = [
        r"quan\s+(?:thu|so)?\s*(\d+)",
        r"\bso\s*(\d+)\b",
        r"#\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized_query)
        if match:
            return int(match.group(1))
    word_ordinals = {
        "dau": 1,
        "dau tien": 1,
        "mot": 1,
        "hai": 2,
        "ba": 3,
        "bon": 4,
        "tu": 4,
        "nam": 5,
    }
    for word, index in word_ordinals.items():
        if f"quan thu {word}" in normalized_query or f"quan {word}" in normalized_query:
            return index
    return None


def _parse_guest_count(normalized_query: str) -> int | None:
    direct_match = re.search(r"(\d{1,2})\s*(?:nguoi|ng|khach)\b", normalized_query)
    if direct_match:
        return int(direct_match.group(1))
    seat_match = re.search(r"(?<!thu\s)(\d{1,2})\s*cho\b", normalized_query)
    if seat_match:
        return int(seat_match.group(1))
    return None


def _parse_reservation_time(query: str) -> datetime | None:
    normalized_query = normalize_text(query).replace(",", " ")
    time_match = re.search(r"\b(?:luc|vao)?\s*(\d{1,2})(?::|h)(\d{2})?\b", normalized_query)
    if not time_match:
        return None
    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    if hour <= 10:
        hour += 12
    if hour > 23 or minute > 59:
        return None

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", normalized_query)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year_raw = date_match.group(3)
        year = int(year_raw) if year_raw else now.year
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None

    target_date = now.date() + (timedelta(days=1) if "mai" in normalized_query else timedelta())
    candidate = datetime.combine(target_date, datetime.min.time()).replace(hour=hour, minute=minute)
    if candidate <= now + timedelta(minutes=30):
        candidate += timedelta(days=1)
    return candidate


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _parse_uuid(value: Any) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_datetime(value: datetime) -> str:
    return value.strftime("%H:%M ngày %d/%m/%Y")


def _looks_like_restaurant_name(query: str) -> bool:
    normalized_query = normalize_text(query)
    return len(normalized_query.split()) <= 8 and not _is_booking_request(normalized_query)
