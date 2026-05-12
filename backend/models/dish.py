# File: models/dish.py (MenuItem)
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class MenuItem(Base):
    __tablename__ = "menu_items"

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True)  # "Đồ ăn", "Nước uống", "Combo"
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)

    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")


# Keep old name as alias for backward compatibility
Dish = MenuItem