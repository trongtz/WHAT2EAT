from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas.auth import UserRegisterRequest, UserLoginRequest, AuthResponse
from core.security import verify_password, create_access_token
from core.database import get_db
import crud.user as crud_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới"""
    # 1. Kiểm tra email bằng hàm CRUD
    if crud_user.get_user_by_email(db, email=payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã tồn tại"
        )
    
    # 2. Tạo User bằng hàm CRUD
    new_user = crud_user.create_user(db, user_in=payload)
    
    # 3. Tạo Token và trả về
    token = create_access_token(data={"sub": str(new_user.user_id)})
    return {"token": token, "user": new_user}


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập vào hệ thống"""
    # 1. Tìm user bằng hàm CRUD
    user = crud_user.get_user_by_email(db, email=payload.email)
    
    # 2. Xác thực
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )
    
    # 3. Check status
    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa, vui lòng liên hệ quản trị viên"
        )
    
    # 4. Tạo Token và trả về
    token = create_access_token(data={"sub": str(user.user_id)})
    return {"token": token, "user": user}


# login dành riêng để test trên swagger
@router.post("/login/swagger", include_in_schema=False)
async def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """API Swagger test login"""
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Tài khoản bị vô hiệu hóa")
    
    token = create_access_token(data={"sub": str(user.user_id)})
    # Swagger bắt buộc key trả về phải tên là "access_token" và "token_type"
    return {"access_token": token, "token_type": "bearer"}