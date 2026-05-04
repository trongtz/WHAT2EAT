from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ai đặt? (Trỏ về User)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Đặt ở đâu? (Trỏ về Restaurant)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    
    # Thông tin chi tiết
    booking_date = Column(String, nullable=False) # Định dạng: YYYY-MM-DD
    booking_time = Column(String, nullable=False) # Định dạng: HH:MM
    number_of_people = Column(Integer, nullable=False)
    note = Column(Text, nullable=True) # Lời nhắn thêm (VD: "Sắp xếp chỗ gần cửa sổ")
    
    # Trạng thái: pending (chờ xác nhận), confirmed (chủ quán đã chốt), cancelled (đã hủy)
    status = Column(String, default="pending") 

    # Thiết lập mối quan hệ
    customer = relationship("User", back_populates="bookings")
    restaurant = relationship("Restaurant", back_populates="bookings")