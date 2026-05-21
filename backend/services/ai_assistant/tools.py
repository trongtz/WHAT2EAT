from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from models.restaurant import Restaurant
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommend_imports import extract_district_slug_from_text
from services.capacity_service import count_booked_tables_for_date, get_restaurant_capacity_for_date


def search_restaurants_tool(db: Session, limit: int = 500) -> list[Restaurant]:
    return crud_restaurant.get_restaurants(db, skip=0, limit=limit)


def check_available_slots_tool(db: Session, restaurant: Restaurant) -> int | None:
    try:
        max_capacity = get_restaurant_capacity_for_date(db, restaurant.restaurant_id)
        booked_capacity = count_booked_tables_for_date(db, restaurant.restaurant_id)
    except Exception:
        return None
    return max(max_capacity - booked_capacity, 0)


def passes_hard_constraints(restaurant: Restaurant, intent: Any) -> bool:
    requested_districts = set(intent_value(intent, "districts", []) or [])
    restaurant_district = extract_district_slug_from_text(restaurant.address)
    if requested_districts and restaurant_district and restaurant_district not in requested_districts:
        return False

    requested_max = intent_value(intent, "price_max")
    price_min, _ = parse_price_range(restaurant.price_range)
    if requested_max is not None and price_min is not None and price_min > int(requested_max):
        return False

    return True


def parse_price_range(price_range: str | None) -> tuple[int | None, int | None]:
    numbers = [int(match) for match in re.findall(r"\d+", str(price_range or ""))]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers[:2]), max(numbers[:2])


def price_budget_label(price_min: int | None, price_max: int | None) -> str | None:
    anchor = price_max if price_max is not None else price_min
    if anchor is None:
        return None
    if anchor <= 100_000:
        return "binh_dan"
    if anchor <= 250_000:
        return "trung_binh"
    if anchor <= 500_000:
        return "kha_cao"
    return "cao_cap"
