import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class CheckIn(Base):
    __tablename__ = "checkins"

    checkin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.reservation_id"), nullable=True)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.item_id"), nullable=True)
    checkin_at = Column(DateTime, server_default=func.now(), nullable=False)
    crowd_status = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    customer = relationship("User")
    restaurant = relationship("Restaurant")
    reservation = relationship("Reservation")
    menu_item = relationship("MenuItem")
