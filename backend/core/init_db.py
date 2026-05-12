# File: core/init_db.py
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
            print("Database đã có dữ liệu mẫu. Bỏ qua bước khởi tạo.")
            return

        print("Đang khởi tạo bộ dữ liệu mẫu (Mock Data)...")

        hashed_pw = get_password_hash("123456")

        admin = User(full_name="Super Admin", email="admin@what2eat.com", password_hash=hashed_pw, role="ADMIN")
        owner = User(full_name="Trần Chủ Quán", email="owner@what2eat.com", password_hash=hashed_pw, role="OWNER")
        customer = User(
            full_name="Nguyễn Thực Khách",
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
              name="Phở Bát Đàn Gia Truyền",
              address="49 Bát Đàn, Hoàn Kiếm, Hà Nội",
              latitude=10.762622,
              longitude=106.660172,
              phone="0123456789",
              description="Phở bò chuẩn vị Bắc.",
              open_hours="06:00 - 10:00",
              images=["https://images.unsplash.com/photo-1628294895950-9805252327bc"],
              cuisine_type="Phở",
              price_range="mid",
              status="APPROVED",
          ),
          Restaurant(
              owner_id=owner.user_id,
              name="Cơm Tấm Ba Ghiền",
              address="84 Đặng Văn Ngữ, Phú Nhuận, TP.HCM",
              latitude=10.793836,
              longitude=106.664875,
              phone="0987654321",
              description="Sườn nướng than hoa.",
              open_hours="07:00 - 21:00",
              images=["https://images.unsplash.com/photo-1626804475297-41609ea004eb"],
              cuisine_type="Cơm",
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

        print("Đã bơm dữ liệu mẫu thành công!")

    except Exception as e:
        db.rollback()
        print(f"Lỗi khi khởi tạo dữ liệu: {e}")
    finally:
        db.close()
