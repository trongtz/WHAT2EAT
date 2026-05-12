# File: models/customer_profile.py
from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from core.database import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    dietary_preferences = Column(JSONB, nullable=True)  # ["chay", "không hải sản", "dị ứng đậu phộng"]
    loyalty_points = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="customer_profile")
