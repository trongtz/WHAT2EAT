import re
from datetime import datetime, time
from uuid import UUID

from sqlalchemy.orm import Session

from models.booking import Reservation
from models.capacity import Capacity


def _normalize_day_of_week(value: datetime) -> int:
    return (value.weekday() + 1) % 7


def parse_open_hours_range(open_hours: str | None) -> tuple[time, time]:
    if not open_hours:
        return time(0, 0), time(23, 59)

    match = re.search(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", open_hours)
    if not match:
        return time(0, 0), time(23, 59)

    start_raw, end_raw = match.groups()
    try:
        return time.fromisoformat(start_raw), time.fromisoformat(end_raw)
    except ValueError:
        return time(0, 0), time(23, 59)


def replace_restaurant_capacities(
    db: Session,
    restaurant_id: UUID,
    open_hours: str | None,
    max_capacity: int,
) -> None:
    start_time, end_time = parse_open_hours_range(open_hours)

    db.query(Capacity).filter(Capacity.restaurant_id == restaurant_id).delete(synchronize_session=False)
    db.flush()

    for day_of_week in range(7):
        db.add(
            Capacity(
                restaurant_id=restaurant_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                max_capacity=max_capacity,
            )
        )

    db.commit()


def get_restaurant_max_capacity(db: Session, restaurant_id: UUID, reference_time: datetime | None = None) -> int:
    target_time = reference_time or datetime.now()
    day_of_week = _normalize_day_of_week(target_time)

    capacity = (
        db.query(Capacity)
        .filter(Capacity.restaurant_id == restaurant_id, Capacity.day_of_week == day_of_week)
        .order_by(Capacity.start_time.asc())
        .first()
    )

    if capacity:
        return int(capacity.max_capacity)

    fallback = (
        db.query(Capacity)
        .filter(Capacity.restaurant_id == restaurant_id)
        .order_by(Capacity.day_of_week.asc(), Capacity.start_time.asc())
        .first()
    )
    return int(fallback.max_capacity) if fallback else 0


def get_restaurant_available_capacity(
    db: Session,
    restaurant_id: UUID,
    reference_time: datetime | None = None,
) -> int:
    target_time = reference_time or datetime.now()
    max_capacity = get_restaurant_max_capacity(db, restaurant_id, target_time)
    if max_capacity <= 0:
        return 0

    reserved_tables = (
        db.query(Reservation)
        .filter(
            Reservation.restaurant_id == restaurant_id,
            Reservation.status.in_(["PENDING", "CONFIRMED"]),
            Reservation.reservation_time >= datetime.combine(target_time.date(), time(0, 0)),
            Reservation.reservation_time <= datetime.combine(target_time.date(), time(23, 59, 59)),
        )
        .count()
    )

    return max(0, max_capacity - int(reserved_tables))


def attach_capacity_summary(db: Session, restaurant) -> None:
    max_capacity = get_restaurant_max_capacity(db, restaurant.restaurant_id)
    available_capacity = get_restaurant_available_capacity(db, restaurant.restaurant_id)
    setattr(restaurant, "max_capacity", max_capacity)
    setattr(restaurant, "available_capacity", available_capacity)


def get_available_capacity_for_slot(
    db: Session,
    restaurant_id: UUID,
    reservation_time: datetime,
) -> int:
    max_capacity = get_restaurant_max_capacity(db, restaurant_id, reservation_time)
    if max_capacity <= 0:
        return 0

    reserved_tables = (
        db.query(Reservation)
        .filter(
            Reservation.restaurant_id == restaurant_id,
            Reservation.status.in_(["PENDING", "CONFIRMED"]),
            Reservation.reservation_time == reservation_time,
        )
        .count()
    )
    return max(0, max_capacity - reserved_tables)
