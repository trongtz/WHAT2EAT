# File: models/favorite.py
from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class Favorite(Base):
    __tablename__ = "favorites"

    favorite_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('customer_id', 'restaurant_id', name='unique_favorite'),
    )

    # Relationships
    customer = relationship("User", back_populates="favorites")
    restaurant = relationship("Restaurant", back_populates="favorites")
