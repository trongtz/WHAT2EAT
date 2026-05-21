from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.search_history as crud_search_history
from api.deps import get_current_user, get_optional_current_user
from core.database import get_db
from models.user import User
from schemas.search_history import SearchHistoryCreate, SearchHistoryResponse

router = APIRouter()


def require_customer(current_user: User) -> None:
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chi khach hang moi co lich su tim kiem")


@router.post("/", response_model=SearchHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_search_history(
    payload: SearchHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    customer_id = current_user.user_id if current_user and current_user.role == "CUSTOMER" else None
    return crud_search_history.create_search_history(db, payload, customer_id)


@router.get("/", response_model=list[SearchHistoryResponse])
def get_my_search_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)
    return crud_search_history.get_search_history_by_customer(db, current_user.user_id, skip=skip, limit=limit)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_my_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)
    crud_search_history.clear_search_history(db, current_user.user_id)
    return None
