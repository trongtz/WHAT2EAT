from pydantic import BaseModel, EmailStr
from typing import Optional

# ==========================================
# 1. SCHEMAS CHO REQUEST (Frontend gửi lên)
# ==========================================

class UserRegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    phone: str
    password: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

# ==========================================
# 2. SCHEMAS CHO RESPONSE (Backend trả về)
# ==========================================

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