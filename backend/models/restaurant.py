from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    
    # ForeignKey trỏ về bảng 'users', cột 'id'
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    
    name = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    opening_time = Column(String, nullable=True) # Ví dụ: "08:00 - 22:00"
    capacity = Column(Integer, default=50) # Sức chứa tối đa (số bàn/người)
    
    # Trạng thái: pending (chờ duyệt), approved (đã duyệt), rejected (bị từ chối)
    status = Column(String, default="pending") 
    image_url = Column(String, nullable=True)

    # Khai báo mối quan hệ để SQLAlchemy tự động lấy dữ liệu chủ quán khi cần
    owner = relationship("User", back_populates="restaurants")