from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # NULL nếu dùng OAuth2
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'facebook'
    oauth_id = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="CUSTOMER")  # ADMIN, OWNER, CUSTOMER
    avatar_url = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, BANNED
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    owner_profile = relationship("OwnerProfile", back_populates="user", uselist=False)
    restaurants = relationship("Restaurant", back_populates="owner")
    reservations = relationship("Reservation", back_populates="customer")
    reviews = relationship("Review", back_populates="customer")
    favorites = relationship("Favorite", back_populates="customer")
    search_history = relationship("SearchHistory", back_populates="customer")
    notifications = relationship("Notification", back_populates="user")