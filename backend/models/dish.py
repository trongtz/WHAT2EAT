from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Khóa ngoại trỏ về nhà hàng
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False) # Giá tiền
    category = Column(String, nullable=True) # Danh mục: Khai vị, Món chính, Đồ uống...
    
    # Quan trọng: Trạng thái Còn hàng / Hết hàng theo đúng Proposal
    is_available = Column(Boolean, default=True) 
    image_url = Column(String, nullable=True)

    # Khai báo mối quan hệ ngược lại với Restaurant
    restaurant = relationship("Restaurant", back_populates="dishes")