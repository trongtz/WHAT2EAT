# File: models/booking.py (Reservation)
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    reservation_time = Column(DateTime, nullable=False)
    guest_count = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    
    status = Column(String(50), default="PENDING")  # PENDING, CONFIRMED, REJECTED, CANCELLED
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("User", back_populates="reservations")
    restaurant = relationship("Restaurant", back_populates="reservations")
    review = relationship("Review", back_populates="reservation", uselist=False)


# Keep old name as alias for backward compatibility
Booking = Reservation