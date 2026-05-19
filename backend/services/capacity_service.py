from datetime import datetime, time
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.booking import Reservation
from models.capacity import Capacity
from models.restaurant import Restaurant


def _parse_open_hours_range(open_hours: str | None) -> tuple[time, time]:
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


def replace_restaurant_capacities(
    db: Session,
    restaurant_id: UUID,
    open_hours: str | None,
    max_capacity: int,
) -> None:
    start_time, end_time = _parse_open_hours_range(open_hours)

    db.query(Capacity).filter(Capacity.restaurant_id == restaurant_id).delete()
    db.add(
        Capacity(
            restaurant_id=restaurant_id,
            day_of_week=0,
            start_time=start_time,
            end_time=end_time,
            max_capacity=max_capacity,
        )
    )
    db.commit()


def attach_capacity_summary(db: Session, restaurant: Restaurant) -> Restaurant:
    max_capacity = get_restaurant_max_capacity(db, restaurant.restaurant_id)
    active_guest_count = (
        db.query(Reservation)
        .filter(
            Reservation.restaurant_id == restaurant.restaurant_id,
            Reservation.status.in_(["PENDING", "CONFIRMED"]),
        )
        .with_entities(func.sum(Reservation.guest_count))
        .scalar()
        or 0
    )
    available_capacity = max(max_capacity - int(active_guest_count), 0)

    setattr(restaurant, "max_capacity", max_capacity)
    setattr(restaurant, "available_capacity", available_capacity)
    return restaurant
