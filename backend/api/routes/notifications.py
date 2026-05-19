from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.notification as crud_notification
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.notification import NotificationResponse

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
def get_my_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_notification.get_notifications_by_user(
        db,
        current_user.user_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = crud_notification.mark_as_read(db, notification_id, current_user.user_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay thong bao")
    return notification
