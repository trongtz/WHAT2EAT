from __future__ import annotations

import csv
import json
import os
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
BATCH_SIZE = 1000

sys.path.insert(0, str(BACKEND_DIR))

from core.database import SessionLocal
from models.customer_profile import CustomerProfile
from models.review import Review
from models.user import User


def main() -> None:
    db = SessionLocal()
    try:
        users = [_user_row(row) for row in _csv_rows("users.csv")]
        customer_profiles = [_customer_profile_row(row) for row in _csv_rows("customer_profiles.csv")]
        reviews = _deduplicate_reviews([_review_row(row) for row in _csv_rows("reviews.csv")])

        _upsert(db, User, users, ["user_id"])
        _upsert(db, CustomerProfile, customer_profiles, ["customer_id"])
        _upsert(db, Review, reviews, ["customer_id", "restaurant_id"], update_skip_columns=["review_id"])
        db.commit()

        print(f"Synced users: {len(users)}")
        print(f"Synced customer profiles: {len(customer_profiles)}")
        print(f"Synced reviews: {len(reviews)}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _csv_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return [
            row
            for row in csv.DictReader(csv_file)
            if any(str(value or "").strip() for value in row.values())
        ]


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


def _user_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "user_id": _uuid(row.get("user_id")),
        "full_name": _str(row.get("full_name"), ""),
        "email": _str(row.get("email"), ""),
        "password_hash": _str(row.get("password_hash")),
        "oauth_provider": _str(row.get("oauth_provider")),
        "oauth_id": _str(row.get("oauth_id")),
        "role": _str(row.get("role"), "CUSTOMER"),
        "avatar_url": _str(row.get("avatar_url")),
        "status": _str(row.get("status"), "ACTIVE"),
        "created_at": _datetime(row.get("created_at")),
    }


def _customer_profile_row(row: dict[str, str]) -> dict[str, Any]:
    return {
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


def _review_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "review_id": _uuid(row.get("review_id")),
        "customer_id": _uuid(row.get("customer_id")),
        "restaurant_id": _uuid(row.get("restaurant_id")),
        "reservation_id": _uuid(row.get("reservation_id")),
        "rating": _int(row.get("rating"), 5),
        "comment": _str(row.get("comment")),
        "status": _str(row.get("status"), "APPROVED"),
        "rejection_reason": _str(row.get("rejection_reason")),
        "created_at": _datetime(row.get("created_at")),
        "updated_at": _datetime(row.get("updated_at")),
    }


def _deduplicate_reviews(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[tuple[uuid.UUID | None, uuid.UUID | None], dict[str, Any]] = {}
    for row in rows:
        key = (row.get("customer_id"), row.get("restaurant_id"))
        current = deduplicated.get(key)
        if current is None:
            deduplicated[key] = row
            continue

        current_time = current.get("updated_at") or current.get("created_at") or datetime.min
        next_time = row.get("updated_at") or row.get("created_at") or datetime.min
        if next_time >= current_time:
            deduplicated[key] = row
    return list(deduplicated.values())


def _upsert(
    db,
    model: type,
    rows: list[dict[str, Any]],
    conflict_columns: list[str],
    update_skip_columns: list[str] | None = None,
) -> None:
    if not rows:
        return

    table = model.__table__
    update_skip_columns = update_skip_columns or []
    grouped_rows: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        clean_row = {key: value for key, value in row.items() if value is not None}
        grouped_rows.setdefault(tuple(clean_row.keys()), []).append(clean_row)

    for grouped_chunk in grouped_rows.values():
        for start in range(0, len(grouped_chunk), BATCH_SIZE):
            chunk = grouped_chunk[start : start + BATCH_SIZE]
            insert_statement = pg_insert(table)
            update_columns = {
                column.name: getattr(insert_statement.excluded, column.name)
                for column in table.columns
                if column.name not in conflict_columns and column.name not in update_skip_columns
            }
            statement = (
                insert_statement
                .values(chunk)
                .on_conflict_do_update(index_elements=conflict_columns, set_=update_columns)
            )
            db.execute(statement)


if __name__ == "__main__":
    os.chdir(BACKEND_DIR)
    main()
