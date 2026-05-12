from uuid import UUID
from sqlalchemy.orm import Session
from models.user import User
from models.customer_profile import CustomerProfile
from models.owner_profile import OwnerProfile
from schemas.auth import UserRegisterRequest
from core.security import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    """Tìm user theo email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Tìm user theo user_id"""
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(db: Session, user_in: UserRegisterRequest) -> User:
    """Tạo user mới vào database"""
    hashed_password = get_password_hash(user_in.password)
    
    # Validate role
    role = user_in.role.upper() if user_in.role in ["CUSTOMER", "OWNER", "customer", "owner"] else "CUSTOMER"
    
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_password,
        role=role,
        status="ACTIVE"
    )
    db.add(db_user)
    db.flush()  # Generate user_id trước khi tạo profile
    
    # Tạo profile tương ứng
    if role == "CUSTOMER":
        customer_profile = CustomerProfile(customer_id=db_user.user_id)
        db.add(customer_profile)
    elif role == "OWNER":
        owner_profile = OwnerProfile(owner_id=db_user.user_id)
        db.add(owner_profile)
    
    db.commit()
    db.refresh(db_user)
    return db_user
