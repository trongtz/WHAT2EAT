from __future__ import annotations

from typing import Any


DAY_KEYS = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")


def format_time_range(value: Any) -> str | None:
    if not value:
        return None

    text = str(value).strip()
    if not text or text.lower() == "closed":
        return None

    if "-" not in text:
        return text

    start_raw, end_raw = [part.strip() for part in text.split("-", 1)]
    if not start_raw or not end_raw:
        return text
    return f"{start_raw} - {end_raw}"


def get_primary_open_hours(opening_hours: Any) -> str | None:
    if isinstance(opening_hours, str):
        return format_time_range(opening_hours)

    if not isinstance(opening_hours, dict):
        return None

    for key in ("regular", "main", "default", "primary"):
        value = opening_hours.get(key)
        if isinstance(value, dict):
            range_text = format_time_range(
                f"{value.get('open')} - {value.get('close')}"
                if value.get("open") and value.get("close")
                else None
            )
        else:
            range_text = format_time_range(value)
        if range_text:
            return range_text

    day_ranges = []
    for day_key in DAY_KEYS:
        value = opening_hours.get(day_key)
        if isinstance(value, dict):
            range_text = format_time_range(
                f"{value.get('open')} - {value.get('close')}"
                if value.get("open") and value.get("close")
                else None
            )
        else:
            range_text = format_time_range(value)
        if range_text:
            day_ranges.append(range_text)

    if not day_ranges:
        return None

    counts = {range_text: day_ranges.count(range_text) for range_text in set(day_ranges)}
    return max(counts, key=counts.get)


def normalize_opening_hours(opening_hours: Any) -> dict[str, Any] | None:
    primary_open_hours = get_primary_open_hours(opening_hours)
    if not primary_open_hours:
        return None

    special_days = []
    if isinstance(opening_hours, dict):
        special_days = opening_hours.get("special_days") or opening_hours.get("specialDays") or []

    return {
        "regular": primary_open_hours,
        "special_days": special_days if isinstance(special_days, list) else [],
    }
