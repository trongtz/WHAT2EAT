from __future__ import annotations

import argparse
import math
import sys
import uuid
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")

import models.registry  # noqa: F401,E402
from core.config import settings  # noqa: E402
from models.customer_profile import CustomerProfile  # noqa: E402
from models.dish import MenuItem  # noqa: E402
from models.restaurant import Restaurant  # noqa: E402
from models.review import Review  # noqa: E402
from models.user import User  # noqa: E402

MAX_REVIEWS_PER_CUSTOMER = 5
REVIEWER_NAMESPACE = uuid.UUID("c627b22e-3772-44c7-aa9c-7d291bcb7850")
REVIEWER_EMAIL_DOMAIN = "what2eat.demo"

engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize demo reviews and restaurant price ranges.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this flag, only prints a summary.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        review_count = db.query(Review).count()
        max_reviews_on_restaurant = (
            db.query(func.count(Review.review_id))
            .group_by(Review.restaurant_id)
            .order_by(func.count(Review.review_id).desc())
            .limit(1)
            .scalar()
            or 0
        )
        required_customers = max(
            math.ceil(review_count / MAX_REVIEWS_PER_CUSTOMER) if review_count else 0,
            int(max_reviews_on_restaurant),
        )
        current_customers = _customer_users(db)
        reviewers_to_create = max(required_customers - len(current_customers), 0)

        print(f"reviews_total={review_count}")
        print(f"current_customers={len(current_customers)}")
        print(f"required_customers={required_customers}")
        print(f"reviewers_to_create={reviewers_to_create}")

        price_updates = _restaurant_price_range_updates(db)
        print(f"price_range_updates={len(price_updates)}")

        if not args.apply:
            print("dry_run=true")
            return

        if reviewers_to_create:
            _create_review_customers(db, reviewers_to_create)
            db.flush()

        review_updates = _rebalance_reviews(db)
        rating_updates = _sync_restaurant_ratings(db)
        price_updates = _sync_restaurant_price_ranges(db)
        db.commit()

        print(f"review_customer_updates={review_updates}")
        print(f"rating_updates={rating_updates}")
        print(f"price_range_updates={price_updates}")
        _print_review_distribution(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()


def _customer_users(db) -> list[User]:
    return (
        db.query(User)
        .filter(User.role == "CUSTOMER", User.status == "ACTIVE")
        .order_by(User.email)
        .all()
    )


def _reviewer_user_id(index: int) -> uuid.UUID:
    return uuid.uuid5(REVIEWER_NAMESPACE, f"reviewer-{index:04d}")


def _create_review_customers(db, count: int) -> None:
    user_rows = []
    profile_rows = []
    existing_emails = {
        email
        for (email,) in db.query(User.email).filter(User.email.like(f"reviewer%@{REVIEWER_EMAIL_DOMAIN}")).all()
    }
    existing_user_ids = {user_id for (user_id,) in db.query(User.user_id).all()}
    created = 0
    index = 1
    while created < count:
        user_id = _reviewer_user_id(index)
        email = f"reviewer{index:04d}@{REVIEWER_EMAIL_DOMAIN}"
        if email in existing_emails or user_id in existing_user_ids:
            index += 1
            continue

        user_rows.append(
            {
                "user_id": user_id,
                "full_name": f"Review Customer {index:04d}",
                "email": email,
                "password_hash": None,
                "role": "CUSTOMER",
                "status": "ACTIVE",
            }
        )
        profile_rows.append({"customer_id": user_id})
        existing_emails.add(email)
        existing_user_ids.add(user_id)
        created += 1
        index += 1

    if user_rows:
        db.bulk_insert_mappings(User, user_rows)
        db.bulk_insert_mappings(CustomerProfile, profile_rows)


def _rebalance_reviews(db) -> int:
    customers = _customer_users(db)
    customer_ids = [customer.user_id for customer in customers]
    customer_emails = {customer.user_id: customer.email for customer in customers}
    generated_customer_ids = [
        customer.user_id
        for customer in customers
        if customer.email.startswith("reviewer") and customer.email.endswith(f"@{REVIEWER_EMAIL_DOMAIN}")
    ]
    counts: Counter[uuid.UUID] = Counter()
    restaurant_customers: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    update_rows = []
    delete_ids = []

    reviews = (
        db.query(Review.review_id, Review.customer_id, Review.restaurant_id)
        .order_by(Review.restaurant_id, Review.created_at, Review.review_id)
        .all()
    )

    for review in reviews:
        if (
            review.customer_id in customer_ids
            and counts[review.customer_id] < MAX_REVIEWS_PER_CUSTOMER
            and review.customer_id not in restaurant_customers[review.restaurant_id]
        ):
            next_customer_id = review.customer_id
        else:
            next_customer_id = _choose_customer(
                generated_customer_ids or customer_ids,
                customer_emails,
                counts,
                restaurant_customers[review.restaurant_id],
            )

        if next_customer_id is None:
            delete_ids.append(review.review_id)
            continue

        if review.customer_id != next_customer_id:
            update_rows.append(
                {
                    "review_id": review.review_id,
                    "customer_id": next_customer_id,
                    "reservation_id": None,
                }
            )

        counts[next_customer_id] += 1
        restaurant_customers[review.restaurant_id].add(next_customer_id)

    if delete_ids:
        db.query(Review).filter(Review.review_id.in_(delete_ids)).delete(synchronize_session=False)
    if update_rows:
        db.bulk_update_mappings(Review, update_rows)

    return len(update_rows) + len(delete_ids)


def _choose_customer(
    customer_ids: list[uuid.UUID],
    customer_emails: dict[uuid.UUID, str],
    counts: Counter[uuid.UUID],
    used_on_restaurant: set[uuid.UUID],
) -> uuid.UUID | None:
    candidates = [
        customer_id
        for customer_id in customer_ids
        if counts[customer_id] < MAX_REVIEWS_PER_CUSTOMER and customer_id not in used_on_restaurant
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda customer_id: (counts[customer_id], customer_emails[customer_id]))


def _sync_restaurant_ratings(db) -> int:
    stats = {
        row.restaurant_id: row.average_rating
        for row in (
            db.query(Review.restaurant_id, func.avg(Review.rating).label("average_rating"))
            .filter(Review.status != "REJECTED")
            .group_by(Review.restaurant_id)
            .all()
        )
    }

    update_rows = []
    for restaurant_id, current_rating in db.query(Restaurant.restaurant_id, Restaurant.rating_avg).all():
        average_rating = stats.get(restaurant_id)
        next_rating = Decimal("0.00") if average_rating is None else Decimal(str(round(float(average_rating), 2)))
        if current_rating != next_rating:
            update_rows.append({"restaurant_id": restaurant_id, "rating_avg": next_rating})

    if update_rows:
        db.bulk_update_mappings(Restaurant, update_rows)
    return len(update_rows)


def _restaurant_price_range_updates(db) -> list[tuple[uuid.UUID, str]]:
    updates = []
    rows = (
        db.query(
            Restaurant.restaurant_id,
            Restaurant.price_range,
            func.min(MenuItem.price),
            func.max(MenuItem.price),
        )
        .join(MenuItem, MenuItem.restaurant_id == Restaurant.restaurant_id)
        .group_by(Restaurant.restaurant_id, Restaurant.price_range)
        .all()
    )
    for restaurant_id, current_price_range, min_price, max_price in rows:
        if min_price is None or max_price is None:
            continue
        next_price_range = _price_range_label(min_price, max_price)
        if current_price_range != next_price_range:
            updates.append((restaurant_id, next_price_range))
    return updates


def _sync_restaurant_price_ranges(db) -> int:
    updates = _restaurant_price_range_updates(db)
    if updates:
        db.bulk_update_mappings(
            Restaurant,
            [{"restaurant_id": restaurant_id, "price_range": price_range} for restaurant_id, price_range in updates],
        )
    return len(updates)


def _price_range_label(min_price: Decimal, max_price: Decimal) -> str:
    return f"{int(min_price)} - {int(max_price)}"


def _print_review_distribution(db) -> None:
    over_limit = (
        db.query(Review.customer_id, func.count(Review.review_id))
        .group_by(Review.customer_id)
        .having(func.count(Review.review_id) > MAX_REVIEWS_PER_CUSTOMER)
        .count()
    )
    reviewer_count = db.query(Review.customer_id).distinct().count()
    print(f"customers_over_{MAX_REVIEWS_PER_CUSTOMER}={over_limit}")
    print(f"customers_with_reviews={reviewer_count}")


if __name__ == "__main__":
    main()
