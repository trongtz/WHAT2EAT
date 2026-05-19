from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.ai_chat as crud_ai_chat
from api.deps import get_current_user, get_optional_current_user
from core.database import get_db
from models.user import User
from schemas.ai_chat import (
    AIChatMessageCreate,
    AIChatMessageResponse,
    AIChatSessionCreate,
    AIChatSessionResponse,
    AIChatSessionUpdate,
    RecommendationLogCreate,
    RecommendationLogResponse,
)

router = APIRouter()


def ensure_session_access(session, current_user: User | None) -> None:
    if session.customer_id is None:
        return
    if current_user is None or session.customer_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong co quyen truy cap phien AI nay")


@router.post("/sessions", response_model=AIChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_ai_session(
    payload: AIChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    customer_id = current_user.user_id if current_user and current_user.role == "CUSTOMER" else None
    return crud_ai_chat.create_session(db, payload, customer_id)


@router.get("/sessions", response_model=list[AIChatSessionResponse])
def get_my_ai_sessions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chi khach hang moi co lich su AI")
    return crud_ai_chat.get_sessions_by_customer(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/sessions/{session_id}", response_model=AIChatSessionResponse)
def get_ai_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    session = crud_ai_chat.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay phien AI")
    ensure_session_access(session, current_user)
    return session


@router.put("/sessions/{session_id}", response_model=AIChatSessionResponse)
def update_ai_session(
    session_id: UUID,
    payload: AIChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    session = crud_ai_chat.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay phien AI")
    ensure_session_access(session, current_user)
    return crud_ai_chat.update_session(db, session, payload)


@router.post("/sessions/{session_id}/messages", response_model=AIChatMessageResponse, status_code=status.HTTP_201_CREATED)
def create_ai_message(
    session_id: UUID,
    payload: AIChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    session = crud_ai_chat.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay phien AI")
    ensure_session_access(session, current_user)
    return crud_ai_chat.create_message(db, session_id, payload)


@router.get("/sessions/{session_id}/messages", response_model=list[AIChatMessageResponse])
def get_ai_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    session = crud_ai_chat.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay phien AI")
    ensure_session_access(session, current_user)
    return crud_ai_chat.get_messages(db, session_id, skip=skip, limit=limit)


@router.post("/recommendation-logs", response_model=RecommendationLogResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation_log(
    payload: RecommendationLogCreate,
    db: Session = Depends(get_db),
):
    return crud_ai_chat.create_recommendation_log(db, payload)


@router.get("/sessions/{session_id}/recommendation-logs", response_model=list[RecommendationLogResponse])
def get_recommendation_logs(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    session = crud_ai_chat.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay phien AI")
    ensure_session_access(session, current_user)
    return crud_ai_chat.get_recommendation_logs(db, session_id, skip=skip, limit=limit)
