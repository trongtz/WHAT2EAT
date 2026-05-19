from datetime import time

from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.security import get_password_hash
from models.capacity import Capacity
from models.customer_profile import CustomerProfile
from models.owner_profile import OwnerProfile
from models.restaurant import Restaurant
from models.user import User


def seed_data():
    db: Session = SessionLocal()
    try:
        if db.query(User).first() or db.query(Restaurant).first():
            print("Database already has seed data. Skipping initialization.")
            return

        print("Initializing seed data...")

        hashed_pw = get_password_hash("123456")

        admin = User(full_name="Super Admin", email="admin@what2eat.com", password_hash=hashed_pw, role="ADMIN")
        owner = User(full_name="Tran Chu Quan", email="owner@what2eat.com", password_hash=hashed_pw, role="OWNER")
        customer = User(
            full_name="Nguyen Thuc Khach",
            email="customer@what2eat.com",
            password_hash=hashed_pw,
            role="CUSTOMER",
        )

        db.add_all([admin, owner, customer])
        db.commit()
        db.refresh(owner)
        db.refresh(customer)

        owner_profile = OwnerProfile(owner_id=owner.user_id)
        customer_profile = CustomerProfile(customer_id=customer.user_id)
        db.add_all([owner_profile, customer_profile])

        restaurants = [
            Restaurant(
                owner_id=owner.user_id,
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
                owner_id=owner.user_id,
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

        db.refresh(restaurants[0])
        db.refresh(restaurants[1])
        capacities = [
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
        db.add_all(capacities)
        db.commit()

        print("Seed data initialized successfully.")

    except Exception as error:
        db.rollback()
        print(f"Seed initialization error: {error}")
    finally:
        db.close()
