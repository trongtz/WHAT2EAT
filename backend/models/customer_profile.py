from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.db_types import json_column_type


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    dietary_preferences = Column(json_column_type(), nullable=True)
    preferred_cuisines = Column(json_column_type(), nullable=True)
    preferred_price_range = Column(String(50), nullable=True)
    preferred_locations = Column(json_column_type(), nullable=True)
    loyalty_points = Column(Integer, nullable=False, default=0)
    personalization_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="customer_profile")
