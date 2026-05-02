from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from models.user import User

# Khai báo nơi để Swagger UI biết đường gọi API lấy Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/swagger")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Hàm này tự động lấy Token từ Header, giải mã và tìm User trong CSDL"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc đã hết hạn)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã Token bằng SECRET_KEY
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = str(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Tìm user trong Database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user