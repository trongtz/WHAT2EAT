from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    phone: str
    password: str = Field(..., max_length=50)
    role: Literal["customer", "owner"] = "customer"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserData(BaseModel):
    id: int
    fullName: str
    email: EmailStr
    phone: str
    role: str
    status: str


class AuthResponse(BaseModel):
    token: str
    user: UserData
