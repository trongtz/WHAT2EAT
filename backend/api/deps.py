from __future__ import annotations

from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from models.user import User
import crud.user as crud_user

# Khai báo nơi để Swagger UI biết đường gọi API lấy Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/swagger")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login/swagger", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Hàm này tự động lấy Token từ Header, giải mã và tìm User trong CSDL"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc đã hết hạn)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã Token bằng SECRET_KEY
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert string to UUID
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Tìm user trong Database
    user = crud_user.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )
    
    return user


def get_optional_current_user(token: str | None = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        return None

    user = crud_user.get_user_by_id(db, user_id=user_id)
    if user is None or user.status != "ACTIVE":
        return None
    return user
