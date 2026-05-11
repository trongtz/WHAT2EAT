# File: models/capacity.py
from sqlalchemy import Column, String, Integer, Time, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class Capacity(Base):
    __tablename__ = "capacities"

    capacity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    day_of_week = Column(Integer, nullable=False)  # 0=CN, 1=T2, ..., 6=T7
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_capacity = Column(Integer, nullable=False)  # 0 = ngừng nhận đặt chỗ

    __table_args__ = (
        UniqueConstraint('restaurant_id', 'day_of_week', 'start_time', 'end_time', name='unique_capacity'),
    )

    # Relationships
    restaurant = relationship("Restaurant", back_populates="capacities")


class CapacityOverride(Base):
    __tablename__ = "capacity_overrides"

    override_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    override_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_capacity = Column(Integer, nullable=False)  # 0 = đóng cửa
    note = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('restaurant_id', 'override_date', 'start_time', 'end_time', name='unique_override'),
    )

    # Relationships
    restaurant = relationship("Restaurant", back_populates="capacity_overrides")
