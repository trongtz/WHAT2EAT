import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class RestaurantImage(Base):
    __tablename__ = "restaurant_images"

    image_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    image_url = Column(Text, nullable=False)
    image_type = Column(String(50), nullable=False, default="general")
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)

    restaurant = relationship("Restaurant", back_populates="restaurant_images")


class CuisineCategory(Base):
    __tablename__ = "cuisine_categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)


class RestaurantCuisine(Base):
    __tablename__ = "restaurant_cuisines"

    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("cuisine_categories.category_id"), primary_key=True)

    restaurant = relationship("Restaurant", back_populates="cuisine_links")
    category = relationship("CuisineCategory")
