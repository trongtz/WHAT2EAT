from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.notification import Notification


def create_notification(
    db: Session,
    user_id: UUID,
    notification_type: str,
    title: str,
    content: str,
    reference_id: UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        content=content,
        reference_id=reference_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications_by_user(
    db: Session,
    user_id: UUID,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification | None:
    notification = (
        db.query(Notification)
        .filter(Notification.notification_id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        return None

    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
