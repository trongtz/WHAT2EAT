from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models.dish import Dish
from models.restaurant import Restaurant
from models.user import User
from schemas.dish import DishCreate, DishResponse
from api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    dish_in: DishCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Bắt buộc đăng nhập
):
    """API Thêm món ăn mới vào Thực đơn (Chỉ Owner của nhà hàng đó mới được thêm)"""
    
    # 1. Kiểm tra nhà hàng có tồn tại không
    restaurant = db.query(Restaurant).filter(Restaurant.id == dish_in.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà hàng này")
        
    # 2. BẢO MẬT: Kiểm tra xem người đang đăng nhập có đúng là Chủ của nhà hàng này không?
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thêm món ăn vào nhà hàng của người khác")
        
    # 3. Thêm món ăn
    db_dish = Dish(**dish_in.model_dump())
    db.add(db_dish)
    db.commit()
    db.refresh(db_dish)
    return db_dish

@router.get("/restaurant/{restaurant_id}", response_model=List[DishResponse])
def get_dishes_by_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """API Lấy toàn bộ thực đơn của một nhà hàng (Cho Khách hàng xem)"""
    return db.query(Dish).filter(Dish.restaurant_id == restaurant_id).all()