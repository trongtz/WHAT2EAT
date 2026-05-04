from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.booking import Booking
from schemas.booking import BookingCreate, BookingResponse
from api.deps import get_current_user
import crud.booking as crud_booking

router = APIRouter()

# ==========================================
# LUỒNG KHÁCH HÀNG (CUSTOMER)
# ==========================================

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Yêu cầu đăng nhập
):
    """API Đặt bàn mới (Chỉ dành cho Khách hàng)"""
    
    # 1. Kiểm tra Nhà hàng có tồn tại không
    restaurant = db.query(Restaurant).filter(Restaurant.id == booking_in.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà hàng này")
        
    # 2. Tạo đơn đặt bàn, tự động gán ID của người đang đăng nhập
    return crud_booking.create_booking(db=db, booking=booking_in, customer_id=current_user.id)

@router.get("/my-bookings", response_model=List[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API Xem lịch sử đặt bàn của Khách hàng"""
    return crud_booking.get_bookings_by_customer(db, customer_id=current_user.id)

# ==========================================
# LUỒNG CHỦ QUÁN (OWNER)
# ==========================================

@router.get("/restaurant/{restaurant_id}", response_model=List[BookingResponse])
def get_restaurant_bookings(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API Xem danh sách đặt bàn (Chỉ Chủ quán của nhà hàng đó mới xem được)"""
    
    # 1. Kiểm tra nhà hàng
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà hàng")
        
    # 2. BẢO MẬT: Kiểm tra xem người đang đăng nhập có đúng là Chủ của nhà hàng này không?
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem dữ liệu của nhà hàng này")
        
    return crud_booking.get_bookings_by_restaurant(db, restaurant_id=restaurant_id)

@router.put("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    new_status: str, # Trạng thái mới: "confirmed" hoặc "cancelled"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API Cập nhật trạng thái đơn đặt bàn (Xác nhận/Từ chối)"""
    
    # 1. Tìm đơn đặt bàn
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt bàn")
        
    # 2. Tìm nhà hàng của đơn đặt bàn đó
    restaurant = db.query(Restaurant).filter(Restaurant.id == booking.restaurant_id).first()
    
    # 3. BẢO MẬT: Phải là Chủ của nhà hàng đó mới được duyệt đơn
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thay đổi trạng thái đơn này")
        
    # 4. Kiểm tra trạng thái hợp lệ
    valid_statuses = ["pending", "confirmed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
        
    return crud_booking.update_booking_status(db, booking_id=booking_id, status=new_status)