# File: models/restaurant.py
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    restaurant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=False)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    open_hours = Column(Text, nullable=True)
    images = Column(JSONB, nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    price_range = Column(String(20), nullable=True)
    average_rating = Column(Numeric(3, 2), default=0.0)

    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="restaurants")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    capacities = relationship("Capacity", back_populates="restaurant", cascade="all, delete-orphan")
    capacity_overrides = relationship("CapacityOverride", back_populates="restaurant", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")
