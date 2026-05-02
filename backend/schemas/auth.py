from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    phone: str
    password: str = Field(..., max_length=50)
    role: Optional[str] = "customer" 

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

