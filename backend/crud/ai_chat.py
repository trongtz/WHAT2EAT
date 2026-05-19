from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from models.ai_chat import AIChatMessage, AIChatSession, RecommendationLog
from schemas.ai_chat import AIChatMessageCreate, AIChatSessionCreate, AIChatSessionUpdate, RecommendationLogCreate


def create_session(db: Session, payload: AIChatSessionCreate, customer_id: UUID | None) -> AIChatSession:
    session = AIChatSession(customer_id=customer_id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: UUID) -> AIChatSession | None:
    return db.query(AIChatSession).filter(AIChatSession.session_id == session_id).first()


def get_sessions_by_customer(db: Session, customer_id: UUID, skip: int = 0, limit: int = 50) -> list[AIChatSession]:
    return (
        db.query(AIChatSession)
        .filter(AIChatSession.customer_id == customer_id)
        .order_by(AIChatSession.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_session(db: Session, session: AIChatSession, payload: AIChatSessionUpdate) -> AIChatSession:
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("status"):
        update_data["status"] = update_data["status"].upper()
        if update_data["status"] == "ENDED":
            update_data["ended_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(session, field, value)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_message(db: Session, session_id: UUID, payload: AIChatMessageCreate) -> AIChatMessage:
    message = AIChatMessage(session_id=session_id, **payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, session_id: UUID, skip: int = 0, limit: int = 100) -> list[AIChatMessage]:
    return (
        db.query(AIChatMessage)
        .filter(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_recommendation_log(db: Session, payload: RecommendationLogCreate) -> RecommendationLog:
    log = RecommendationLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_recommendation_logs(db: Session, session_id: UUID, skip: int = 0, limit: int = 100) -> list[RecommendationLog]:
    return (
        db.query(RecommendationLog)
        .filter(RecommendationLog.session_id == session_id)
        .order_by(RecommendationLog.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
