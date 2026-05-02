from sqlalchemy.orm import Session
from models.user import User
from schemas.auth import UserRegisterRequest
from core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    """Tìm user theo email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserRegisterRequest):
    """Tạo user mới vào database"""
    hashed_password = get_password_hash(user_in.password)
    
    assigned_role = user_in.role if user_in.role in ["customer", "owner"] else "customer"
    
    db_user = User(
        fullName=user_in.fullName,
        email=user_in.email,
        phone=user_in.phone,
        password=hashed_password,
        role=assigned_role,
        status="active"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user