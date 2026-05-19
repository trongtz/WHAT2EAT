from uuid import UUID

from sqlalchemy.orm import Session

from models.moderation_log import ModerationLog
from schemas.moderation import ModerationLogCreate


def create_log(db: Session, payload: ModerationLogCreate, admin_id: UUID) -> ModerationLog:
    log = ModerationLog(
        admin_id=admin_id,
        target_type=payload.target_type.lower(),
        target_id=payload.target_id,
        action=payload.action.upper(),
        reason=payload.reason,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs(db: Session, skip: int = 0, limit: int = 100) -> list[ModerationLog]:
    return (
        db.query(ModerationLog)
        .order_by(ModerationLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
