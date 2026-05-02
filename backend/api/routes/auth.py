from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.auth import UserRegisterRequest, UserLoginRequest, AuthResponse
from core.security import verify_password, create_access_token
from core.database import get_db
import crud.user as crud_user 

router = APIRouter()

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    # 1. Kiểm tra email bằng hàm CRUD
    if crud_user.get_user_by_email(db, email=payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"message": "Email này đã tồn tại"}
        )
    
    # 2. Tạo User bằng hàm CRUD
    new_user = crud_user.create_user(db, user_in=payload)
    
    # 3. Tạo Token và trả về
    token = create_access_token(data={"sub": str(new_user.id)})
    return {"token": token, "user": new_user}

@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    # 1. Tìm user bằng hàm CRUD
    user = crud_user.get_user_by_email(db, email=payload.email)
    
    # 2. Xác thực
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={"message": "Email hoặc mật khẩu không đúng"}
        )
        
    # 3. Tạo Token và trả về
    token = create_access_token(data={"sub": str(user.id)})
    return {"token": token, "user": user}