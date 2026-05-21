from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AliasChoices, BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

import crud.user as crud_user
from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.auth import UserData

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, validation_alias=AliasChoices("full_name", "fullName"))
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, validation_alias=AliasChoices("avatar_url", "avatarUrl"))

    model_config = {"populate_by_name": True, "extra": "ignore"}


@router.get("/me", response_model=UserData)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserData)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    full_name = payload.full_name.strip() if payload.full_name else None
    if full_name is not None and not full_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name is required")

    if payload.email and payload.email != current_user.email:
        existing_user = crud_user.get_user_by_email(db, payload.email)
        if existing_user and existing_user.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        current_user.email = payload.email

    if full_name is not None:
        current_user.full_name = full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url.strip() or None

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
