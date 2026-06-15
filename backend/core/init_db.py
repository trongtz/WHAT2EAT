from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.security import get_password_hash
from models.ai_chat import AIChatMessage, AIChatSession, RecommendationLog
from models.booking import Reservation
from models.capacity import Capacity, CapacityOverride
from models.checkin import CheckIn
from models.customer_profile import CustomerProfile
from models.dish import MenuItem
from models.favorite import Favorite
from models.moderation_log import ModerationLog
from models.notification import Notification
from models.owner_profile import OwnerProfile
from models.restaurant import Restaurant
from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine, RestaurantImage
from models.review import Review
from models.search_history import SearchHistory
from models.user import User
from services.opening_hours_service import normalize_opening_hours


RowBuilder = Callable[[dict[str, str]], Any]
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


def _identity_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _int(value: Any, default: int | None = None) -> int | None:
    text = _clean(value)
    return int(text) if text is not None else default


def _decimal(value: Any, default: str | None = None) -> Decimal | None:
    text = _clean(value)
    if text is None:
        text = default
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


def _csv_rows(data_dir: str, filename: str) -> list[dict[str, str]]:
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        print(f"Seed file missing, skipped: {filename}")
        return []

    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        return [
            row
            for row in csv.DictReader(csv_file)
            if any(str(value or "").strip() for value in row.values())
        ]


def _model_values(item: Any) -> dict[str, Any]:
    values = {}
    for column in item.__table__.columns:
        value = getattr(item, column.name)
        if value is not None:
            values[column.name] = value
    return values


def _insert_ignore_conflicts(
    db: Session,
    model: type,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0

    inserted = 0
    table = model.__table__
    grouped_rows: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped_rows.setdefault(tuple(row.keys()), []).append(row)

    for grouped_chunk in grouped_rows.values():
        for start in range(0, len(grouped_chunk), BATCH_SIZE):
            chunk = grouped_chunk[start : start + BATCH_SIZE]
            statement = pg_insert(table).values(chunk).on_conflict_do_nothing()
            result = db.execute(statement)
            inserted += result.rowcount or 0
    return inserted


def _add_by_primary_key(
    db: Session,
    data_dir: str,
    filename: str,
    model: type,
    primary_key: str,
    build: RowBuilder,
    duplicate_key: Callable[[Any], tuple[str, ...] | None] | None = None,
) -> int:
    rows = []
    seen_duplicate_keys: set[tuple[str, ...]] = set()
    for row in _csv_rows(data_dir, filename):
        item = build(row)
        key_value = getattr(item, primary_key)
        if key_value is None:
            continue
        if duplicate_key is not None:
            item_duplicate_key = duplicate_key(item)
            if item_duplicate_key:
                if item_duplicate_key in seen_duplicate_keys:
                    continue
                seen_duplicate_keys.add(item_duplicate_key)
        rows.append(_model_values(item))

    added = _insert_ignore_conflicts(db, model, rows)
    db.commit()
    print(f"Imported {added} rows from {filename}.")
    return added


def _import_restaurant_cuisines(db: Session, data_dir: str) -> int:
    rows = []
    for row in _csv_rows(data_dir, "restaurant_cuisines.csv"):
        restaurant_id = _uuid(row.get("restaurant_id"))
        category_id = _uuid(row.get("category_id"))
        if restaurant_id is None or category_id is None:
            continue
        rows.append({"restaurant_id": restaurant_id, "category_id": category_id})

    added = _insert_ignore_conflicts(db, RestaurantCuisine, rows)
    db.commit()
    print("Imported " + str(added) + " rows from restaurant_cuisines.csv.")
    return added


def _create_minimal_seed(db: Session) -> None:
    password_hash = get_password_hash("123456")
    admin_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    db.add_all(
        [
            User(
                user_id=admin_id,
                full_name="Super Admin",
                email="admin@what2eat.com",
                password_hash=password_hash,
                role="ADMIN",
                status="ACTIVE",
            ),
            User(
                user_id=owner_id,
                full_name="Default Owner",
                email="owner@what2eat.com",
                password_hash=password_hash,
                role="OWNER",
                status="ACTIVE",
            ),
            User(
                user_id=customer_id,
                full_name="Default Customer",
                email="customer@what2eat.com",
                password_hash=password_hash,
                role="CUSTOMER",
                status="ACTIVE",
            ),
            OwnerProfile(owner_id=owner_id),
            CustomerProfile(customer_id=customer_id),
        ]
    )
    db.commit()
    print("Minimal seed data initialized because users.csv was not found.")


def _sync_seed_user_passwords(db: Session, data_dir: str) -> int:
    updated = 0
    for row in _csv_rows(data_dir, "users.csv"):
        email = _str(row.get("email"))
        password_hash = _str(row.get("password_hash"))
        if not email or not password_hash:
            continue

        user = db.query(User).filter(User.email == email).first()
        if user and user.password_hash != password_hash:
            user.password_hash = password_hash
            updated += 1

    if updated:
        db.commit()
        print(f"Synchronized password hashes for {updated} seeded users.")
    return updated


def _sync_seed_restaurant_images(db: Session, data_dir: str) -> int:
    changed = 0
    for row in _csv_rows(data_dir, "restaurant_images.csv"):
        image_id = _uuid(row.get("image_id"))
        restaurant_id = _uuid(row.get("restaurant_id"))
        image_url = _str(row.get("image_url"))
        if not image_id or not restaurant_id or not image_url:
            continue

        image = db.get(RestaurantImage, image_id)
        if image:
            if image.image_url != image_url:
                image.image_url = image_url
                image.image_type = _str(row.get("image_type"), image.image_type)
                changed += 1
            continue

        if db.get(Restaurant, restaurant_id):
            db.add(
                RestaurantImage(
                    image_id=image_id,
                    restaurant_id=restaurant_id,
                    image_url=image_url,
                    image_type=_str(row.get("image_type"), "general"),
                    uploaded_at=_datetime(row.get("uploaded_at")),
                )
            )
            changed += 1

    if changed:
        db.commit()
        print(f"Synchronized {changed} seeded restaurant images.")
    return changed


def _price_range_label(min_price: Decimal, max_price: Decimal) -> str:
    return f"{int(min_price)} - {int(max_price)}"


def _sync_restaurant_price_ranges(db: Session) -> int:
    changed = 0
    price_ranges = (
        db.query(
            MenuItem.restaurant_id,
            func.min(MenuItem.price),
            func.max(MenuItem.price),
        )
        .group_by(MenuItem.restaurant_id)
        .all()
    )

    for restaurant_id, min_price, max_price in price_ranges:
        if min_price is None or max_price is None:
            continue
        restaurant = db.get(Restaurant, restaurant_id)
        if not restaurant:
            continue
        next_price_range = _price_range_label(min_price, max_price)
        if restaurant.price_range != next_price_range:
            restaurant.price_range = next_price_range
            changed += 1

    if changed:
        db.commit()
        print(f"Synchronized price ranges for {changed} restaurants from menu items.")
    return changed


def _import_csv_seed(db: Session, data_dir: str) -> None:
    _add_by_primary_key(
        db,
        data_dir,
        "users.csv",
        User,
        "user_id",
        lambda row: User(
            user_id=_uuid(row.get("user_id")),
            full_name=_str(row.get("full_name"), ""),
            email=_str(row.get("email"), ""),
            password_hash=_str(row.get("password_hash")),
            oauth_provider=_str(row.get("oauth_provider")),
            oauth_id=_str(row.get("oauth_id")),
            role=_str(row.get("role"), "CUSTOMER"),
            avatar_url=_str(row.get("avatar_url")),
            status=_str(row.get("status"), "ACTIVE"),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "customer_profiles.csv",
        CustomerProfile,
        "customer_id",
        lambda row: CustomerProfile(
            customer_id=_uuid(row.get("customer_id")),
            dietary_preferences=_json(row.get("dietary_preferences")),
            preferred_cuisines=_json(row.get("preferred_cuisines")),
            preferred_price_range=_str(row.get("preferred_price_range")),
            preferred_locations=_json(row.get("preferred_locations")),
            loyalty_points=_int(row.get("loyalty_points"), 0),
            personalization_enabled=_bool(row.get("personalization_enabled"), True),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "owner_profiles.csv",
        OwnerProfile,
        "owner_id",
        lambda row: OwnerProfile(
            owner_id=_uuid(row.get("owner_id")),
            tax_id=_str(row.get("tax_id")),
            business_license=_str(row.get("business_license")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "cuisine_categories.csv",
        CuisineCategory,
        "category_id",
        lambda row: CuisineCategory(
            category_id=_uuid(row.get("category_id")),
            name=_str(row.get("name"), ""),
            description=_str(row.get("description")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "restaurants.csv",
        Restaurant,
        "restaurant_id",
        lambda row: Restaurant(
            restaurant_id=_uuid(row.get("restaurant_id")),
            owner_id=_uuid(row.get("owner_id")),
            name=_str(row.get("name"), ""),
            description=_str(row.get("description")),
            address=_str(row.get("address"), ""),
            latitude=_decimal(row.get("latitude")),
            longitude=_decimal(row.get("longitude")),
            phone=_str(row.get("phone")),
            opening_hours=normalize_opening_hours(_json(row.get("opening_hours"))),
            price_range=_str(row.get("price_range")),
            rating_avg=_decimal(row.get("rating_avg"), "0"),
            approval_status=_str(row.get("approval_status"), "PENDING"),
            is_active=_bool(row.get("is_active"), True),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
        duplicate_key=lambda item: (_identity_text(item.name), _identity_text(item.address)),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "restaurant_images.csv",
        RestaurantImage,
        "image_id",
        lambda row: RestaurantImage(
            image_id=_uuid(row.get("image_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            image_url=_str(row.get("image_url"), ""),
            image_type=_str(row.get("image_type"), "general"),
            uploaded_at=_datetime(row.get("uploaded_at")),
        ),
    )
    _import_restaurant_cuisines(db, data_dir)
    _add_by_primary_key(
        db,
        data_dir,
        "menu_items.csv",
        MenuItem,
        "item_id",
        lambda row: MenuItem(
            item_id=_uuid(row.get("item_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            name=_str(row.get("name"), ""),
            description=_str(row.get("description")),
            price=_decimal(row.get("price"), "0"),
            category=_str(row.get("category")),
            image_url=_str(row.get("image_url")),
            availability_status=_str(row.get("availability_status"), "AVAILABLE"),
        ),
    )
    _sync_restaurant_price_ranges(db)
    _add_by_primary_key(
        db,
        data_dir,
        "capacities.csv",
        Capacity,
        "capacity_id",
        lambda row: Capacity(
            capacity_id=_uuid(row.get("capacity_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            day_of_week=_int(row.get("day_of_week"), 0),
            start_time=_time(row.get("start_time")),
            end_time=_time(row.get("end_time")),
            max_capacity=_int(row.get("max_capacity"), 0),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "capacity_overrides.csv",
        CapacityOverride,
        "override_id",
        lambda row: CapacityOverride(
            override_id=_uuid(row.get("override_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            override_date=_date(row.get("override_date")),
            start_time=_time(row.get("start_time")),
            end_time=_time(row.get("end_time")),
            max_capacity=_int(row.get("max_capacity"), 0),
            note=_str(row.get("note")),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "reservations.csv",
        Reservation,
        "reservation_id",
        lambda row: Reservation(
            reservation_id=_uuid(row.get("reservation_id")),
            customer_id=_uuid(row.get("customer_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            reservation_time=_datetime(row.get("reservation_time")),
            guest_count=_int(row.get("guest_count"), 1),
            notes=_str(row.get("notes")),
            status=_str(row.get("status"), "PENDING"),
            rejection_reason=_str(row.get("rejection_reason")),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "reviews.csv",
        Review,
        "review_id",
        lambda row: Review(
            review_id=_uuid(row.get("review_id")),
            customer_id=_uuid(row.get("customer_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            reservation_id=_uuid(row.get("reservation_id")),
            rating=_int(row.get("rating"), 5),
            comment=_str(row.get("comment")),
            status=_str(row.get("status"), "PENDING"),
            rejection_reason=_str(row.get("rejection_reason")),
            created_at=_datetime(row.get("created_at")),
            updated_at=_datetime(row.get("updated_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "favorites.csv",
        Favorite,
        "favorite_id",
        lambda row: Favorite(
            favorite_id=_uuid(row.get("favorite_id")),
            customer_id=_uuid(row.get("customer_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "search_history.csv",
        SearchHistory,
        "search_id",
        lambda row: SearchHistory(
            search_id=_uuid(row.get("search_id")),
            customer_id=_uuid(row.get("customer_id")),
            query_text=_str(row.get("query_text"), ""),
            search_type=_str(row.get("search_type"), "NORMAL"),
            filters_applied=_json(row.get("filters_applied")),
            extracted_entities=_json(row.get("extracted_entities")),
            result_restaurant_ids=_json(row.get("result_restaurant_ids")),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "checkins.csv",
        CheckIn,
        "checkin_id",
        lambda row: CheckIn(
            checkin_id=_uuid(row.get("checkin_id")),
            customer_id=_uuid(row.get("customer_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            reservation_id=_uuid(row.get("reservation_id")),
            menu_item_id=_uuid(row.get("menu_item_id")),
            checkin_at=_datetime(row.get("checkin_at")),
            crowd_status=_str(row.get("crowd_status")),
            note=_str(row.get("note")),
            is_verified=_bool(row.get("is_verified"), False),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "notifications.csv",
        Notification,
        "notification_id",
        lambda row: Notification(
            notification_id=_uuid(row.get("notification_id")),
            user_id=_uuid(row.get("user_id")),
            type=_str(row.get("type"), ""),
            title=_str(row.get("title"), ""),
            content=_str(row.get("content"), ""),
            reference_id=_uuid(row.get("reference_id")),
            is_read=_bool(row.get("is_read"), False),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "ai_chat_sessions.csv",
        AIChatSession,
        "session_id",
        lambda row: AIChatSession(
            session_id=_uuid(row.get("session_id")),
            customer_id=_uuid(row.get("customer_id")),
            title=_str(row.get("title")),
            context_summary=_str(row.get("context_summary")),
            status=_str(row.get("status"), "ACTIVE"),
            started_at=_datetime(row.get("started_at")),
            ended_at=_datetime(row.get("ended_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "ai_chat_messages.csv",
        AIChatMessage,
        "message_id",
        lambda row: AIChatMessage(
            message_id=_uuid(row.get("message_id")),
            session_id=_uuid(row.get("session_id")),
            role=_str(row.get("role"), "USER"),
            content=_str(row.get("content"), ""),
            extracted_intent=_json(row.get("extracted_intent")),
            processing_status=_str(row.get("processing_status"), "SUCCESS"),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "recommendation_logs.csv",
        RecommendationLog,
        "log_id",
        lambda row: RecommendationLog(
            log_id=_uuid(row.get("log_id")),
            session_id=_uuid(row.get("session_id")),
            customer_id=_uuid(row.get("customer_id")),
            restaurant_id=_uuid(row.get("restaurant_id")),
            score=_decimal(row.get("score")),
            reason=_str(row.get("reason")),
            source=_str(row.get("source")),
            rank_position=_int(row.get("rank_position")),
            prompt_summary=_str(row.get("prompt_summary")),
            model_version=_str(row.get("model_version")),
            created_at=_datetime(row.get("created_at")),
        ),
    )
    _add_by_primary_key(
        db,
        data_dir,
        "moderation_logs.csv",
        ModerationLog,
        "log_id",
        lambda row: ModerationLog(
            log_id=_uuid(row.get("log_id")),
            admin_id=_uuid(row.get("admin_id")),
            target_type=_str(row.get("target_type"), ""),
            target_id=_uuid(row.get("target_id")),
            action=_str(row.get("action"), ""),
            reason=_str(row.get("reason")),
            created_at=_datetime(row.get("created_at")),
        ),
    )


def seed_data(force_import: bool = False) -> None:
    db: Session = SessionLocal()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    force_import = force_import or os.getenv("WHAT2EAT_FORCE_SEED_IMPORT", "").lower() in {"1", "true", "yes"}

    try:
        if db.query(User).first() or db.query(Restaurant).first():
            if os.path.exists(os.path.join(data_dir, "users.csv")):
                print("Database already has seed data. Importing missing CSV rows with conflict-safe batch inserts...")
                _import_csv_seed(db, data_dir)
                _sync_seed_user_passwords(db, data_dir)
                if os.path.exists(os.path.join(data_dir, "restaurant_images.csv")):
                    _sync_seed_restaurant_images(db, data_dir)
                print("CSV seed sync completed.")
                return
            if os.path.exists(os.path.join(data_dir, "restaurant_images.csv")):
                _sync_seed_restaurant_images(db, data_dir)
            print("Database already has seed data. Skipping initialization.")
            return

        if not os.path.exists(os.path.join(data_dir, "users.csv")):
            _create_minimal_seed(db)
            return

        print("Initializing database from backend/data CSV files...")
        _import_csv_seed(db, data_dir)
        print("CSV seed data initialized successfully.")
    except (IntegrityError, ValueError, TypeError) as error:
        db.rollback()
        print(f"Seed initialization error: {error}")
        raise
    finally:
        db.close()
