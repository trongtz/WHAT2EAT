# File: models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = "users" # Tên bảng trong PostgreSQL

    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password = Column(String, nullable=False) # Cột này sẽ lưu mật khẩu đã băm (hashed)
    role = Column(String, default="customer")
    status = Column(String, default="active")

    restaurants = relationship("Restaurant", back_populates="owner") # 1 User (Owner) -> Nhiều Restaurant
    bookings = relationship("Booking", back_populates="customer") # 1 Khách hàng có thể có nhiều lịch đặt bàn