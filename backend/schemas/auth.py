from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("full_name", "fullName"),
    )
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    role: Literal["CUSTOMER", "OWNER"] = "CUSTOMER"

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        if isinstance(value, str):
            return value.upper()
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserData(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: str
    status: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    token: str
    user: UserData

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # expiration time
