from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.booking import Reservation
from models.capacity import Capacity, CapacityOverride
from models.restaurant import Restaurant
from services.opening_hours_service import get_primary_open_hours


def _parse_open_hours_range(open_hours) -> tuple[time, time]:
    open_hours = get_primary_open_hours(open_hours)

    if not open_hours or "-" not in open_hours:
        return time(0, 0), time(23, 59)

    try:
        start_raw, end_raw = [part.strip() for part in open_hours.split("-", 1)]
        start_time = datetime.strptime(start_raw, "%H:%M").time()
        end_time = datetime.strptime(end_raw, "%H:%M").time()
        return start_time, end_time
    except ValueError:
        return time(0, 0), time(23, 59)


def get_restaurant_max_capacity(db: Session, restaurant_id: UUID) -> int:
    capacity = (
        db.query(Capacity)
        .filter(Capacity.restaurant_id == restaurant_id)
        .order_by(Capacity.max_capacity.desc())
        .first()
    )
    return int(capacity.max_capacity) if capacity else 0


def _day_of_week_for_capacity(value: date) -> int:
    return (value.weekday() + 1) % 7


def get_restaurant_capacity_for_date(
    db: Session,
    restaurant_id: UUID,
    target_date: date | None = None,
) -> int:
    target_date = target_date or date.today()
    override = (
        db.query(CapacityOverride)
        .filter(
            CapacityOverride.restaurant_id == restaurant_id,
            CapacityOverride.override_date == target_date,
        )
        .order_by(CapacityOverride.max_capacity.desc())
        .first()
    )
    if override:
        return int(override.max_capacity)

    capacity = (
        db.query(Capacity)
        .filter(
            Capacity.restaurant_id == restaurant_id,
            Capacity.day_of_week == _day_of_week_for_capacity(target_date),
        )
        .order_by(Capacity.max_capacity.desc())
        .first()
    )
    if capacity:
        return int(capacity.max_capacity)

    return get_restaurant_max_capacity(db, restaurant_id)


def replace_restaurant_capacities(
    db: Session,
    restaurant_id: UUID,
    open_hours,
    max_capacity: int,
) -> None:
    start_time, end_time = _parse_open_hours_range(open_hours)

    db.query(Capacity).filter(Capacity.restaurant_id == restaurant_id).delete()
    db.add_all(
        [
            Capacity(
                restaurant_id=restaurant_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                max_capacity=max_capacity,
            )
            for day_of_week in range(7)
        ]
    )
    db.commit()


def count_booked_tables_for_date(
    db: Session,
    restaurant_id: UUID,
    target_date: date | None = None,
) -> int:
    target_date = target_date or date.today()
    start_datetime = datetime.combine(target_date, time.min)
    end_datetime = start_datetime + timedelta(days=1)
    booked_capacity = (
        db.query(func.sum(Reservation.guest_count))
        .filter(
            Reservation.restaurant_id == restaurant_id,
            Reservation.reservation_time >= start_datetime,
            Reservation.reservation_time < end_datetime,
            Reservation.status.in_(["PENDING", "CONFIRMED"]),
        )
        .scalar()
        or 0
    )
    return int(booked_capacity)


def attach_capacity_summary(db: Session, restaurant: Restaurant) -> Restaurant:
    max_capacity = get_restaurant_capacity_for_date(db, restaurant.restaurant_id)
    booked_capacity = count_booked_tables_for_date(db, restaurant.restaurant_id)
    available_capacity = max(max_capacity - booked_capacity, 0)

    setattr(restaurant, "max_capacity", max_capacity)
    setattr(restaurant, "available_capacity", available_capacity)
    setattr(restaurant, "max_tables", max_capacity)
    setattr(restaurant, "available_tables", available_capacity)
    return restaurant
