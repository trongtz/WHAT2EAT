from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys
from typing import Iterable

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")

import models.registry  # noqa: F401,E402
from core.database import SessionLocal  # noqa: E402
from models.ai_chat import RecommendationLog  # noqa: E402
from models.booking import Reservation  # noqa: E402
from models.capacity import Capacity, CapacityOverride  # noqa: E402
from models.checkin import CheckIn  # noqa: E402
from models.dish import MenuItem  # noqa: E402
from models.favorite import Favorite  # noqa: E402
from models.restaurant import Restaurant  # noqa: E402
from models.restaurant_taxonomy import RestaurantCuisine, RestaurantImage  # noqa: E402
from models.review import Review  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge duplicate restaurants by normalized name and address.")
    parser.add_argument("--apply", action="store_true", help="Apply database changes. Without this flag, only prints a summary.")
    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Create a unique expression index after duplicates are removed.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        duplicate_groups = _duplicate_groups(db.query(Restaurant).all())
        duplicate_count = sum(len(group) - 1 for group in duplicate_groups)
        print(f"duplicate_groups={len(duplicate_groups)}")
        print(f"duplicate_restaurants={duplicate_count}")

        for group in duplicate_groups[:10]:
            keeper = _keeper(group)
            print(f"keep={keeper.restaurant_id} merge={len(group) - 1} name={keeper.name!r}")

        if not args.apply:
            print("dry_run=true")
            return

        merged = 0
        for group in duplicate_groups:
            merged += _merge_group(db, group)

        db.commit()
        print(f"merged_restaurants={merged}")

        if args.create_index:
            _create_unique_index(db)
            db.commit()
            print("unique_index=created_or_already_exists")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _duplicate_groups(restaurants: Iterable[Restaurant]) -> list[list[Restaurant]]:
    grouped: dict[tuple[str, str], list[Restaurant]] = defaultdict(list)
    for restaurant in restaurants:
        grouped[_restaurant_key(restaurant)].append(restaurant)

    return [group for group in grouped.values() if len(group) > 1]


def _restaurant_key(restaurant: Restaurant) -> tuple[str, str]:
    return (_identity_text(restaurant.name), _identity_text(restaurant.address))


def _identity_text(value: object) -> str:
    return str(value or "").strip().lower()


def _keeper(restaurants: list[Restaurant]) -> Restaurant:
    return sorted(
        restaurants,
        key=lambda item: (
            item.created_at is None,
            item.created_at,
            str(item.restaurant_id),
        ),
    )[0]


def _merge_group(db, restaurants: list[Restaurant]) -> int:
    keeper = _keeper(restaurants)
    duplicates = [restaurant for restaurant in restaurants if restaurant.restaurant_id != keeper.restaurant_id]
    for duplicate in duplicates:
        _merge_conflicting_favorites(db, keeper.restaurant_id, duplicate.restaurant_id)
        _merge_conflicting_capacities(db, keeper.restaurant_id, duplicate.restaurant_id)
        _merge_conflicting_capacity_overrides(db, keeper.restaurant_id, duplicate.restaurant_id)
        _merge_conflicting_cuisines(db, keeper.restaurant_id, duplicate.restaurant_id)
        _merge_conflicting_images(db, keeper.restaurant_id, duplicate.restaurant_id)
        _merge_conflicting_reviews(db, keeper.restaurant_id, duplicate.restaurant_id)

        _move_rows(db, MenuItem, keeper.restaurant_id, duplicate.restaurant_id)
        _move_rows(db, Reservation, keeper.restaurant_id, duplicate.restaurant_id)
        _move_rows(db, CheckIn, keeper.restaurant_id, duplicate.restaurant_id)
        _move_rows(db, RecommendationLog, keeper.restaurant_id, duplicate.restaurant_id)

        db.delete(duplicate)

    return len(duplicates)


def _move_rows(db, model: type, keeper_id, duplicate_id) -> None:
    db.query(model).filter(model.restaurant_id == duplicate_id).update(
        {model.restaurant_id: keeper_id},
        synchronize_session=False,
    )


def _merge_conflicting_favorites(db, keeper_id, duplicate_id) -> None:
    keeper_customers = {
        row.customer_id
        for row in db.query(Favorite.customer_id).filter(Favorite.restaurant_id == keeper_id).all()
    }
    for favorite in db.query(Favorite).filter(Favorite.restaurant_id == duplicate_id).all():
        if favorite.customer_id in keeper_customers:
            db.delete(favorite)
        else:
            favorite.restaurant_id = keeper_id


def _merge_conflicting_capacities(db, keeper_id, duplicate_id) -> None:
    keeper_slots = {
        (row.day_of_week, row.start_time, row.end_time)
        for row in db.query(Capacity.day_of_week, Capacity.start_time, Capacity.end_time)
        .filter(Capacity.restaurant_id == keeper_id)
        .all()
    }
    for capacity in db.query(Capacity).filter(Capacity.restaurant_id == duplicate_id).all():
        key = (capacity.day_of_week, capacity.start_time, capacity.end_time)
        if key in keeper_slots:
            db.delete(capacity)
        else:
            capacity.restaurant_id = keeper_id


def _merge_conflicting_capacity_overrides(db, keeper_id, duplicate_id) -> None:
    keeper_slots = {
        (row.override_date, row.start_time, row.end_time)
        for row in db.query(CapacityOverride.override_date, CapacityOverride.start_time, CapacityOverride.end_time)
        .filter(CapacityOverride.restaurant_id == keeper_id)
        .all()
    }
    for override in db.query(CapacityOverride).filter(CapacityOverride.restaurant_id == duplicate_id).all():
        key = (override.override_date, override.start_time, override.end_time)
        if key in keeper_slots:
            db.delete(override)
        else:
            override.restaurant_id = keeper_id


def _merge_conflicting_cuisines(db, keeper_id, duplicate_id) -> None:
    keeper_categories = {
        row.category_id
        for row in db.query(RestaurantCuisine.category_id).filter(RestaurantCuisine.restaurant_id == keeper_id).all()
    }
    for cuisine in db.query(RestaurantCuisine).filter(RestaurantCuisine.restaurant_id == duplicate_id).all():
        if cuisine.category_id in keeper_categories:
            db.delete(cuisine)
        else:
            cuisine.restaurant_id = keeper_id


def _merge_conflicting_images(db, keeper_id, duplicate_id) -> None:
    keeper_urls = {
        _identity_text(row.image_url)
        for row in db.query(RestaurantImage.image_url).filter(RestaurantImage.restaurant_id == keeper_id).all()
    }
    for image in db.query(RestaurantImage).filter(RestaurantImage.restaurant_id == duplicate_id).all():
        if _identity_text(image.image_url) in keeper_urls:
            db.delete(image)
        else:
            image.restaurant_id = keeper_id


def _merge_conflicting_reviews(db, keeper_id, duplicate_id) -> None:
    keeper_customers = {
        row.customer_id
        for row in db.query(Review.customer_id).filter(Review.restaurant_id == keeper_id).all()
    }
    for review in db.query(Review).filter(Review.restaurant_id == duplicate_id).all():
        if review.customer_id in keeper_customers:
            db.delete(review)
        else:
            review.restaurant_id = keeper_id


def _create_unique_index(db) -> None:
    db.execute(
        text(
            """
            create unique index if not exists uq_restaurants_name_address
            on restaurants (lower(trim(name)), lower(trim(address)))
            """
        )
    )


if __name__ == "__main__":
    main()
