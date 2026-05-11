# File: models/owner_profile.py
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, ForeignKey
from core.database import Base


class OwnerProfile(Base):
    __tablename__ = "owner_profiles"

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    tax_id = Column(String(20), nullable=True)
    business_license = Column(String(100), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="owner_profile")
