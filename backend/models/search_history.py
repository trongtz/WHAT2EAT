import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.db_types import json_column_type


class SearchHistory(Base):
    __tablename__ = "search_history"

    search_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    query_text = Column(Text, nullable=False)
    search_type = Column(String(20), nullable=False, default="NORMAL")
    filters_applied = Column(json_column_type(), nullable=True)
    extracted_entities = Column(json_column_type(), nullable=True)
    result_restaurant_ids = Column(json_column_type(), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    customer = relationship("User", back_populates="search_history")
