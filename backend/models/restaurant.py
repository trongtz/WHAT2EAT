import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, synonym

from core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    restaurant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    phone = Column(String(20), nullable=True)
    opening_hours = Column(JSONB, nullable=True)
    price_range = Column(String(20), nullable=True)
    rating_avg = Column(Numeric(3, 2), nullable=False, default=0.0)
    approval_status = Column(String(20), nullable=False, default="PENDING")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Compatibility aliases for existing code while DB columns follow Design.md.
    status = synonym("approval_status")
    average_rating = synonym("rating_avg")
    open_hours = synonym("opening_hours")

    owner = relationship("User", back_populates="restaurants")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    capacities = relationship("Capacity", back_populates="restaurant", cascade="all, delete-orphan")
    capacity_overrides = relationship("CapacityOverride", back_populates="restaurant", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")
    restaurant_images = relationship("RestaurantImage", back_populates="restaurant", cascade="all, delete-orphan")
    cuisine_links = relationship("RestaurantCuisine", back_populates="restaurant", cascade="all, delete-orphan")

    @property
    def images(self) -> list[str]:
        return [image.image_url for image in self.restaurant_images]

    @property
    def cuisine_type(self) -> str:
        return ", ".join(link.category.name for link in self.cuisine_links if link.category)
