from typing import Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    role: Literal["CUSTOMER", "OWNER"] = "CUSTOMER"


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

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserData

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # expiration time

