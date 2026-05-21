import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.db_types import json_column_type


class AIChatSession(Base):
    __tablename__ = "ai_chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    title = Column(String(150), nullable=True)
    context_summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    messages = relationship("AIChatMessage", back_populates="session", cascade="all, delete-orphan")
    recommendation_logs = relationship("RecommendationLog", back_populates="session", cascade="all, delete-orphan")


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("ai_chat_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    extracted_intent = Column(json_column_type(), nullable=True)
    processing_status = Column(String(20), nullable=False, default="SUCCESS")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("AIChatSession", back_populates="messages")


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("ai_chat_sessions.session_id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id"), nullable=False)
    score = Column(Numeric(5, 4), nullable=True)
    reason = Column(Text, nullable=True)
    source = Column(String(20), nullable=True)
    rank_position = Column(Integer, nullable=True)
    prompt_summary = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("AIChatSession", back_populates="recommendation_logs")
