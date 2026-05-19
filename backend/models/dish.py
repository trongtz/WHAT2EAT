import uuid

from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from core.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 0), nullable=False)
    category = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    availability_status = Column(String(20), nullable=False, default="AVAILABLE")

    restaurant = relationship("Restaurant", back_populates="menu_items")

    @hybrid_property
    def is_available(self) -> bool:
        return self.availability_status == "AVAILABLE"

    @is_available.setter
    def is_available(self, value: bool) -> None:
        self.availability_status = "AVAILABLE" if value else "UNAVAILABLE"

    @is_available.expression
    def is_available(cls):
        return cls.availability_status == "AVAILABLE"


Dish = MenuItem
