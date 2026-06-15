from __future__ import annotations

import re
import math
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, selectinload

from models.restaurant import Restaurant
from models.restaurant_taxonomy import RestaurantCuisine
from services.ai_assistant.intent_extractor import intent_value
from services.ai_assistant.recommend_imports import dish_aliases, extract_district_slug_from_text, haversine_km, normalize_text
from services.capacity_service import count_booked_tables_for_date, get_restaurant_capacity_for_date
from services.opening_hours_service import get_primary_open_hours


DEFAULT_RADIUS_KM = 2.0

CUISINE_HARD_ALIASES = {
    "ca phe brunch": ["ca phe", "cafe", "coffee", "tra sua", "brunch"],
    "lau": ["lau", "hotpot"],
    "bbq nuong": ["bbq", "nuong", "grill"],
    "mon nhat": ["nhat", "sushi", "ramen", "udon", "japanese"],
    "mon han": ["han quoc", "korean", "kimchi", "tokbokki", "tteokbokki", "mi cay", "seoul", "daegu"],
    "hai san": ["hai san", "seafood", "oc"],
    "chay healthy": ["chay", "healthy", "salad", "vegan", "vegetarian"],
    "mon thai": ["thai", "tomyum", "pad thai"],
    "mon y": ["italy", "italian", "pizza", "pasta"],
    "buffet": ["buffet"],
}


def search_restaurants_tool(
    db: Session,
    limit: int = 10_000,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
) -> list[Restaurant]:
    query = (
        db.query(Restaurant)
        .options(
            selectinload(Restaurant.menu_items),
            selectinload(Restaurant.cuisine_links).selectinload(RestaurantCuisine.category),
        )
        .filter(Restaurant.approval_status == "APPROVED", Restaurant.is_active.is_(True))
    )

    if latitude is not None and longitude is not None and radius_km is not None:
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / max(111.0 * abs(math.cos(math.radians(latitude))), 1.0)
        query = query.filter(
            Restaurant.latitude.isnot(None),
            Restaurant.longitude.isnot(None),
            Restaurant.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Restaurant.longitude.between(longitude - lng_delta, longitude + lng_delta),
        )

    return query.limit(limit).all()


def check_available_slots_tool(db: Session, restaurant: Restaurant) -> int | None:
    try:
        max_capacity = get_restaurant_capacity_for_date(db, restaurant.restaurant_id)
        booked_capacity = count_booked_tables_for_date(db, restaurant.restaurant_id)
    except Exception:
        return None
    return max(max_capacity - booked_capacity, 0)


def passes_hard_constraints(restaurant: Restaurant, intent: Any, *, db: Session | None = None) -> bool:
    if _is_obvious_non_restaurant(restaurant):
        return False

    requested_cuisines = intent_value(intent, "cuisines", []) or []
    if requested_cuisines and not _matches_requested_cuisine(restaurant, requested_cuisines):
        return False
    excluded_cuisines = intent_value(intent, "excluded_cuisines", []) or []
    if excluded_cuisines and _matches_requested_cuisine(restaurant, excluded_cuisines):
        return False

    normalized_text = restaurant_constraint_text(restaurant)
    requested_dishes = intent_value(intent, "dish_terms", []) or []
    if requested_dishes and not any(restaurant_matches_dish(restaurant, dish) for dish in requested_dishes):
        return False
    excluded_keywords = intent_value(intent, "excluded_keywords", []) or []
    if any(_contains_alias(normalized_text, keyword) for keyword in excluded_keywords):
        return False
    preference_tags = intent_value(intent, "preference_tags", []) or []
    if "healthy" in preference_tags and not any(
        _contains_alias(normalized_text, keyword)
        for keyword in ["healthy", "chay", "salad", "rau", "eat clean", "thanh dam", "vegetarian"]
    ):
        return False
    if "soupy_food" in preference_tags and not any(
        _contains_alias(normalized_text, keyword)
        for keyword in ["pho", "bun", "hu tieu", "lau", "canh", "mi", "sup", "soup", "bo kho"]
    ):
        return False

    requested_districts = set(intent_value(intent, "districts", []) or [])
    restaurant_district = extract_district_slug_from_text(restaurant.address)
    if requested_districts and restaurant_district and restaurant_district not in requested_districts:
        return False

    requested_max = intent_value(intent, "price_max")
    price_min, _ = parse_price_range(restaurant.price_range)
    if requested_max is not None and price_min is not None and price_min > int(requested_max):
        return False

    if intent_value(intent, "open_now") and not _is_open_now(restaurant):
        return False

    group_size = intent_value(intent, "group_size")
    if db is not None and group_size is not None:
        available_capacity = check_available_slots_tool(db, restaurant)
        if available_capacity is not None and available_capacity < int(group_size):
            return False

    return True


def _matches_requested_cuisine(restaurant: Restaurant, requested_cuisines: list[str]) -> bool:
    normalized_text = restaurant_identity_text(restaurant)
    for cuisine in requested_cuisines:
        normalized_cuisine = normalize_text(cuisine)
        aliases = CUISINE_HARD_ALIASES.get(normalized_cuisine, [normalized_cuisine])
        if any(_contains_alias(normalized_text, alias) for alias in aliases):
            return True
    return False


def restaurant_identity_text(restaurant: Restaurant) -> str:
    category_text = " ".join(
        link.category.name
        for link in (getattr(restaurant, "cuisine_links", []) or [])
        if getattr(link, "category", None) is not None and getattr(link.category, "name", None)
    )
    return normalize_text(
        " ".join(
            str(part or "")
            for part in [
                restaurant.name,
                restaurant.description,
                getattr(restaurant, "cuisine_type", ""),
                category_text,
            ]
        )
    )


def restaurant_constraint_text(restaurant: Restaurant) -> str:
    return normalize_text(
        " ".join(
            str(part or "")
            for part in [
                restaurant.name,
                restaurant.description,
                getattr(restaurant, "cuisine_type", ""),
                available_menu_text(restaurant),
            ]
        )
    )


def available_menu_text(restaurant: Restaurant, *, limit: int = 40) -> str:
    menu_items = getattr(restaurant, "menu_items", []) or []
    return " ".join(
        f"{item.name} {getattr(item, 'description', '') or ''} {getattr(item, 'category', '') or ''}"
        for item in menu_items[:limit]
        if getattr(item, "availability_status", "AVAILABLE") == "AVAILABLE"
    )


def restaurant_matches_dish(restaurant: Restaurant, dish: str) -> bool:
    aliases = dish_aliases(dish)
    restaurant_text = normalize_text(
        f"{restaurant.name} {restaurant.description or ''} {getattr(restaurant, 'cuisine_type', '')}"
    )
    if any(_contains_alias(restaurant_text, alias) for alias in aliases):
        return True
    for item in (getattr(restaurant, "menu_items", []) or [])[:40]:
        if getattr(item, "availability_status", "AVAILABLE") != "AVAILABLE":
            continue
        item_text = normalize_text(
            f"{item.name} {getattr(item, 'description', '') or ''} {getattr(item, 'category', '') or ''}"
        )
        if any(_contains_alias(item_text, alias) for alias in aliases):
            return True
    return False


def _is_obvious_non_restaurant(restaurant: Restaurant) -> bool:
    normalized_name = normalize_text(getattr(restaurant, "name", "") or "")
    non_restaurant_patterns = [
        "ky tuc xa",
        "truong dai hoc",
        "dai hoc",
        "hoc vien",
        "benh vien",
        "nha thuoc",
        "sieu thi",
        "tram xang",
        "atm",
    ]
    if not any(pattern in normalized_name for pattern in non_restaurant_patterns):
        return False

    food_signals = [
        "quan",
        "cafe",
        "ca phe",
        "coffee",
        "com",
        "bun",
        "pho",
        "mi",
        "lau",
        "tra sua",
        "banh",
        "oc",
        "bbq",
        "sushi",
        "restaurant",
        "food",
    ]
    return not any(signal in normalized_name for signal in food_signals)


def _is_open_now(restaurant: Restaurant) -> bool:
    open_hours = get_primary_open_hours(getattr(restaurant, "opening_hours", None))
    if not open_hours or "-" not in open_hours:
        return True
    try:
        start_raw, end_raw = [part.strip() for part in open_hours.split("-", 1)]
        start_time = datetime.strptime(start_raw, "%H:%M").time()
        end_time = datetime.strptime(end_raw, "%H:%M").time()
    except ValueError:
        return True
    current_time = datetime.now().astimezone().time()
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    return current_time >= start_time or current_time <= end_time


def _contains_alias(normalized_text: str, alias: str) -> bool:
    normalized_alias = normalize_text(alias)
    if not normalized_alias:
        return False
    return re.search(rf"\b{re.escape(normalized_alias)}\b", normalized_text) is not None


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
