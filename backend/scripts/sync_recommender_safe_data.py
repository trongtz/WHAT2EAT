from __future__ import annotations

import csv
import json
import os
import sys
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import models.registry  # noqa: F401
from core.database import SessionLocal
from models.booking import Reservation
from models.capacity import Capacity, CapacityOverride
from models.checkin import CheckIn
from models.customer_profile import CustomerProfile
from models.dish import MenuItem
from models.favorite import Favorite
from models.restaurant import Restaurant
from models.review import Review
from models.search_history import SearchHistory
from models.user import User
from services.opening_hours_service import normalize_opening_hours

BATCH_SIZE = 1000


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _uuid(value: Any) -> uuid.UUID | None:
    text = _clean(value)
    return uuid.UUID(text) if text else None


def _str(value: Any, default: str | None = None) -> str | None:
    text = _clean(value)
    return text if text is not None else default


def _int(value: Any, default: int | None = None) -> int | None:
    text = _clean(value)
    return int(text) if text is not None else default


def _decimal(value: Any, default: str | None = None) -> Decimal | None:
    text = _clean(value) or default
    return Decimal(text) if text is not None else None


def _bool(value: Any, default: bool | None = None) -> bool | None:
    text = _clean(value)
    if text is None:
        return default
    return text.lower() in {"1", "true", "yes", "y", "active", "available"}


def _json(value: Any) -> Any:
    text = _clean(value)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _datetime(value: Any) -> datetime | None:
    text = _clean(value)
    if text is None:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _date(value: Any) -> date | None:
    text = _clean(value)
    return date.fromisoformat(text) if text else None


def _time(value: Any) -> time | None:
    text = _clean(value)
    return time.fromisoformat(text) if text else None


def _csv_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return [
            row
            for row in csv.DictReader(csv_file)
            if any(str(value or "").strip() for value in row.values())
        ]


def _chunked(rows: list[dict[str, Any]], size: int = BATCH_SIZE) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def _dedupe_by_keys(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(row.get(column) for column in keys)
        current = deduped.get(key)
        if current is None:
            deduped[key] = row
            continue
        current_time = current.get("updated_at") or current.get("created_at") or datetime.min
        next_time = row.get("updated_at") or row.get("created_at") or datetime.min
        if next_time >= current_time:
            deduped[key] = row
    return list(deduped.values())


def _upsert(db, model: type, rows: list[dict[str, Any]], conflict_columns: list[str], *, skip_update: list[str] | None = None) -> int:
    if not rows:
        return 0

    table = model.__table__
    skip_update = skip_update or []
    inserted_or_updated = 0

    for chunk in _chunked(rows):
        statement = pg_insert(table)
        update_columns = {
            column.name: getattr(statement.excluded, column.name)
            for column in table.columns
            if column.name not in conflict_columns and column.name not in skip_update
        }
        result = db.execute(
            statement.values(chunk).on_conflict_do_update(
                index_elements=conflict_columns,
                set_=update_columns,
            )
        )
        inserted_or_updated += result.rowcount or 0

    db.commit()
    return inserted_or_updated


def _sync_reviews(db, rows: list[dict[str, Any]]) -> int:
    existing_by_pair = {
        (str(review.customer_id), str(review.restaurant_id)): review
        for review in db.query(Review).all()
    }
    existing_by_id = {
        str(review.review_id): review
        for review in existing_by_pair.values()
        if review.review_id is not None
    }
    synced = 0
    for row in rows:
        pair_key = (str(row["customer_id"]), str(row["restaurant_id"]))
        review = existing_by_pair.get(pair_key)
        if review is None and row.get("review_id") is not None:
            review = existing_by_id.get(str(row["review_id"]))

        if review is None:
            review = Review(**row)
            db.add(review)
            existing_by_pair[pair_key] = review
            if row.get("review_id") is not None:
                existing_by_id[str(row["review_id"])] = review
            synced += 1
            continue

        for key, value in row.items():
            if key == "review_id":
                continue
            setattr(review, key, value)
        db.add(review)
        synced += 1

    db.commit()
    return synced


def main() -> None:
    with SessionLocal() as db:
        existing_restaurant_ids = {str(row[0]) for row in db.query(Restaurant.restaurant_id).all()}
        existing_user_ids = {str(row[0]) for row in db.query(User.user_id).all()}
        existing_reservation_ids = {str(row[0]) for row in db.query(Reservation.reservation_id).all()}
        existing_menu_item_ids = {str(row[0]) for row in db.query(MenuItem.item_id).all()}

        restaurant_rows = [
            {
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "owner_id": _uuid(row.get("owner_id")),
                "name": _str(row.get("name"), ""),
                "description": _str(row.get("description")),
                "address": _str(row.get("address"), ""),
                "latitude": _decimal(row.get("latitude")),
                "longitude": _decimal(row.get("longitude")),
                "phone": _str(row.get("phone")),
                "opening_hours": normalize_opening_hours(_json(row.get("opening_hours"))),
                "price_range": _str(row.get("price_range")),
                "rating_avg": _decimal(row.get("rating_avg"), "0"),
                "approval_status": _str(row.get("approval_status"), "PENDING"),
                "is_active": _bool(row.get("is_active"), True),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("restaurants.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
        ]
        print(f"Restaurants to refresh: {len(restaurant_rows)}")
        _upsert(db, Restaurant, restaurant_rows, ["restaurant_id"])

        menu_rows = [
            {
                "item_id": _uuid(row.get("item_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "name": _str(row.get("name"), ""),
                "description": _str(row.get("description")),
                "price": _decimal(row.get("price"), "0"),
                "category": _str(row.get("category")),
                "image_url": _str(row.get("image_url")),
                "availability_status": _str(row.get("availability_status"), "AVAILABLE"),
            }
            for row in _csv_rows("menu_items.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
        ]
        print(f"Menu items to sync: {len(menu_rows)}")
        _upsert(db, MenuItem, menu_rows, ["item_id"])
        existing_menu_item_ids = {str(row[0]) for row in db.query(MenuItem.item_id).all()}

        capacity_rows = [
            {
                "capacity_id": _uuid(row.get("capacity_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "day_of_week": _int(row.get("day_of_week"), 0),
                "start_time": _time(row.get("start_time")),
                "end_time": _time(row.get("end_time")),
                "max_capacity": _int(row.get("max_capacity"), 0),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("capacities.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
        ]
        print(f"Capacities to sync: {len(capacity_rows)}")
        _upsert(db, Capacity, capacity_rows, ["capacity_id"])

        capacity_override_rows = [
            {
                "override_id": _uuid(row.get("override_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "override_date": _date(row.get("override_date")),
                "start_time": _time(row.get("start_time")),
                "end_time": _time(row.get("end_time")),
                "max_capacity": _int(row.get("max_capacity"), 0),
                "note": _str(row.get("note")),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("capacity_overrides.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
        ]
        print(f"Capacity overrides to sync: {len(capacity_override_rows)}")
        _upsert(db, CapacityOverride, capacity_override_rows, ["override_id"])

        reservation_rows = [
            {
                "reservation_id": _uuid(row.get("reservation_id")),
                "customer_id": _uuid(row.get("customer_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "reservation_time": _datetime(row.get("reservation_time")),
                "guest_count": _int(row.get("guest_count"), 1),
                "notes": _str(row.get("notes")),
                "status": _str(row.get("status"), "PENDING"),
                "rejection_reason": _str(row.get("rejection_reason")),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("reservations.csv")
            if row.get("restaurant_id") in existing_restaurant_ids and row.get("customer_id") in existing_user_ids
        ]
        print(f"Reservations to sync: {len(reservation_rows)}")
        _upsert(db, Reservation, reservation_rows, ["reservation_id"])
        existing_reservation_ids = {str(row[0]) for row in db.query(Reservation.reservation_id).all()}

        review_rows = _dedupe_by_keys([
            {
                "review_id": _uuid(row.get("review_id")),
                "customer_id": _uuid(row.get("customer_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "reservation_id": _uuid(row.get("reservation_id")),
                "rating": _int(row.get("rating"), 5),
                "comment": _str(row.get("comment")),
                "status": _str(row.get("status"), "PENDING"),
                "rejection_reason": _str(row.get("rejection_reason")),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("reviews.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
            and row.get("customer_id") in existing_user_ids
            and (not row.get("reservation_id") or row.get("reservation_id") in existing_reservation_ids)
        ], ["customer_id", "restaurant_id"])
        print(f"Reviews to sync: {len(review_rows)}")
        _sync_reviews(db, review_rows)

        favorite_rows = _dedupe_by_keys([
            {
                "favorite_id": _uuid(row.get("favorite_id")),
                "customer_id": _uuid(row.get("customer_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "created_at": _datetime(row.get("created_at")),
            }
            for row in _csv_rows("favorites.csv")
            if row.get("restaurant_id") in existing_restaurant_ids and row.get("customer_id") in existing_user_ids
        ], ["customer_id", "restaurant_id"])
        print(f"Favorites to sync: {len(favorite_rows)}")
        _upsert(db, Favorite, favorite_rows, ["customer_id", "restaurant_id"], skip_update=["favorite_id"])

        checkin_rows = [
            {
                "checkin_id": _uuid(row.get("checkin_id")),
                "customer_id": _uuid(row.get("customer_id")),
                "restaurant_id": _uuid(row.get("restaurant_id")),
                "reservation_id": _uuid(row.get("reservation_id")),
                "menu_item_id": _uuid(row.get("menu_item_id")),
                "checkin_at": _datetime(row.get("checkin_at")),
                "crowd_status": _str(row.get("crowd_status")),
                "note": _str(row.get("note")),
                "is_verified": _bool(row.get("is_verified"), False),
            }
            for row in _csv_rows("checkins.csv")
            if row.get("restaurant_id") in existing_restaurant_ids
            and row.get("customer_id") in existing_user_ids
            and (not row.get("reservation_id") or row.get("reservation_id") in existing_reservation_ids)
            and (not row.get("menu_item_id") or row.get("menu_item_id") in existing_menu_item_ids)
        ]
        print(f"Checkins to sync: {len(checkin_rows)}")
        _upsert(db, CheckIn, checkin_rows, ["checkin_id"])

        search_history_rows = [
            {
                "search_id": _uuid(row.get("search_id")),
                "customer_id": _uuid(row.get("customer_id")),
                "query_text": _str(row.get("query_text"), ""),
                "search_type": _str(row.get("search_type"), "NORMAL"),
                "filters_applied": _json(row.get("filters_applied")),
                "extracted_entities": _json(row.get("extracted_entities")),
                "result_restaurant_ids": _json(row.get("result_restaurant_ids")),
                "created_at": _datetime(row.get("created_at")),
            }
            for row in _csv_rows("search_history.csv")
            if row.get("customer_id") in existing_user_ids
        ]
        print(f"Search history rows to sync: {len(search_history_rows)}")
        _upsert(db, SearchHistory, search_history_rows, ["search_id"])

        customer_profile_rows = [
            {
                "customer_id": _uuid(row.get("customer_id")),
                "dietary_preferences": _json(row.get("dietary_preferences")),
                "preferred_cuisines": _json(row.get("preferred_cuisines")),
                "preferred_price_range": _str(row.get("preferred_price_range")),
                "preferred_locations": _json(row.get("preferred_locations")),
                "loyalty_points": _int(row.get("loyalty_points"), 0),
                "personalization_enabled": _bool(row.get("personalization_enabled"), True),
                "created_at": _datetime(row.get("created_at")),
                "updated_at": _datetime(row.get("updated_at")),
            }
            for row in _csv_rows("customer_profiles.csv")
            if row.get("customer_id") in existing_user_ids
        ]
        print(f"Customer profiles to sync: {len(customer_profile_rows)}")
        _upsert(db, CustomerProfile, customer_profile_rows, ["customer_id"])

        print("Safe recommender sync completed.")


if __name__ == "__main__":
    main()
