import csv
import os
import uuid
from datetime import time

from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.security import get_password_hash
from models.capacity import Capacity
from models.customer_profile import CustomerProfile
from models.owner_profile import OwnerProfile
from models.restaurant import Restaurant
from models.user import User


def _create_default_accounts(db: Session, password_hash: str) -> tuple[User, User]:
    admin = User(
        user_id=uuid.uuid4(),
        full_name="Super Admin",
        email="admin@what2eat.com",
        password_hash=password_hash,
        role="ADMIN",
    )
    owner = User(
        user_id=uuid.uuid4(),
        full_name="Tran Chu Quan",
        email="owner@what2eat.com",
        password_hash=password_hash,
        role="OWNER",
    )
    customer = User(
        user_id=uuid.uuid4(),
        full_name="Nguyen Thuc Khach",
        email="customer@what2eat.com",
        password_hash=password_hash,
        role="CUSTOMER",
    )

    db.add_all([admin, owner, customer])
    db.commit()
    db.add_all(
        [
            OwnerProfile(owner_id=owner.user_id),
            CustomerProfile(customer_id=customer.user_id),
        ]
    )
    db.commit()
    return owner, customer


def _import_owner_accounts(db: Session, data_dir: str, password_hash: str) -> int:
    owners_csv = os.path.join(data_dir, "generated_owners.csv")
    if not os.path.exists(owners_csv):
        return 0

    owners_added = 0
    with open(owners_csv, newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            owner_id = uuid.UUID(str(row["user_id"]))
            if db.get(User, owner_id):
                continue

            db.add(
                User(
                    user_id=owner_id,
                    full_name=row["full_name"],
                    email=row["email"],
                    password_hash=password_hash,
                    role="OWNER",
                    status="ACTIVE",
                )
            )
            db.add(OwnerProfile(owner_id=owner_id))
            owners_added += 1

    db.commit()
    return owners_added


def _create_sample_restaurants(db: Session, owner_id: uuid.UUID) -> None:
    restaurants = [
        Restaurant(
            owner_id=owner_id,
            name="Pho Bat Dan Gia Truyen",
            address="49 Bat Dan, Hoan Kiem, Ha Noi",
            latitude=10.762622,
            longitude=106.660172,
            phone="0123456789",
            description="Pho bo chuan vi Bac.",
            open_hours="06:00 - 10:00",
            images=["https://images.unsplash.com/photo-1628294895950-9805252327bc"],
            cuisine_type="Pho",
            price_range="mid",
            status="APPROVED",
        ),
        Restaurant(
            owner_id=owner_id,
            name="Com Tam Ba Ghien",
            address="84 Dang Van Ngu, Phu Nhuan, TP.HCM",
            latitude=10.793836,
            longitude=106.664875,
            phone="0987654321",
            description="Suon nuong than hoa.",
            open_hours="07:00 - 21:00",
            images=["https://images.unsplash.com/photo-1626804475297-41609ea004eb"],
            cuisine_type="Com",
            price_range="mid",
            status="APPROVED",
        ),
    ]
    db.add_all(restaurants)
    db.commit()

    for restaurant in restaurants:
        db.refresh(restaurant)

    db.add_all(
        [
            Capacity(
                restaurant_id=restaurants[0].restaurant_id,
                day_of_week=1,
                start_time=time(6, 0),
                end_time=time(10, 0),
                max_capacity=40,
            ),
            Capacity(
                restaurant_id=restaurants[1].restaurant_id,
                day_of_week=1,
                start_time=time(7, 0),
                end_time=time(21, 0),
                max_capacity=60,
            ),
        ]
    )
    db.commit()


def seed_data():
    db: Session = SessionLocal()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    try:
        if db.query(User).first() or db.query(Restaurant).first():
            print("Database already has seed data. Skipping initialization.")
            return

        print("Initializing seed data...")
        password_hash = get_password_hash("123456")
        owner, _ = _create_default_accounts(db, password_hash)
        owners_added = _import_owner_accounts(db, data_dir, password_hash)
        _create_sample_restaurants(db, owner.user_id)

        print(f"Seed data initialized successfully. Imported owners: {owners_added}.")
    except Exception as error:
        db.rollback()
        print(f"Seed initialization error: {error}")
    finally:
        db.close()
