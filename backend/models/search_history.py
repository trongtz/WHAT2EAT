# File: models/search_history.py
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class SearchHistory(Base):
    __tablename__ = "search_history"

    search_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    query_text = Column(Text, nullable=False)
    extracted_entities = Column(JSONB, nullable=True)  # {"type": "lẩu", "weather": "mưa"}
    result_restaurant_ids = Column(JSONB, nullable=True)  # ["uuid1", "uuid2"]
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    customer = relationship("User", back_populates="search_history")
