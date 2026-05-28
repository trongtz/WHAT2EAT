from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

import crud.restaurant as crud_restaurant
from models.restaurant import Restaurant
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommend_imports import extract_district_slug_from_text, haversine_km, normalize_text
from services.capacity_service import count_booked_tables_for_date, get_restaurant_capacity_for_date


DEFAULT_RADIUS_KM = 2.0

CUISINE_HARD_ALIASES = {
    "ca phe brunch": ["ca phe", "cafe", "coffee", "tra sua", "brunch"],
    "lau": ["lau", "hotpot"],
    "bbq nuong": ["bbq", "nuong", "grill"],
    "mon nhat": ["nhat", "sushi", "ramen", "udon", "japanese"],
    "mon han": ["han", "korean", "kimchi", "tokbokki"],
    "hai san": ["hai san", "seafood", "oc"],
    "chay healthy": ["chay", "healthy", "salad", "vegan", "vegetarian"],
    "mon thai": ["thai", "tomyum", "pad thai"],
    "mon y": ["italy", "italian", "pizza", "pasta"],
}


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
    requested_cuisines = intent_value(intent, "cuisines", []) or []
    if requested_cuisines and not _matches_requested_cuisine(restaurant, requested_cuisines):
        return False

    requested_districts = set(intent_value(intent, "districts", []) or [])
    restaurant_district = extract_district_slug_from_text(restaurant.address)
    if requested_districts and restaurant_district and restaurant_district not in requested_districts:
        return False

    requested_max = intent_value(intent, "price_max")
    price_min, _ = parse_price_range(restaurant.price_range)
    if requested_max is not None and price_min is not None and price_min > int(requested_max):
        return False

    return True


def _matches_requested_cuisine(restaurant: Restaurant, requested_cuisines: list[str]) -> bool:
    normalized_text = normalize_text(
        " ".join(
            str(part or "")
            for part in [
                restaurant.name,
                restaurant.description,
                getattr(restaurant, "cuisine_type", ""),
            ]
        )
    )
    for cuisine in requested_cuisines:
        normalized_cuisine = normalize_text(cuisine)
        aliases = CUISINE_HARD_ALIASES.get(normalized_cuisine, [normalized_cuisine])
        if any(alias in normalized_text for alias in aliases):
            return True
    return False


def parse_radius_km_from_query(query: str, *, default_radius_km: float = DEFAULT_RADIUS_KM) -> float:
    normalized = str(query or "").lower().replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(km|m)\b", normalized)
    if not match:
        return default_radius_km

    value = float(match.group(1))
    unit = match.group(2)
    if unit == "m":
        value /= 1000.0
    return min(max(value, 0.1), 20.0)


def passes_location_constraint(
    restaurant: Restaurant,
    *,
    latitude: float | None,
    longitude: float | None,
    radius_km: float | None,
) -> bool:
    if latitude is None or longitude is None or radius_km is None:
        return True

    distance_km = haversine_km(
        latitude,
        longitude,
        _to_float(restaurant.latitude),
        _to_float(restaurant.longitude),
    )
    return distance_km is not None and distance_km <= radius_km


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


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
